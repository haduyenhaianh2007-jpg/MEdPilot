import os
import json
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib

class DiseaseIndexerCombined:
    def __init__(self, 
                 db_path: str = "./chroma_db",
                 cache_path: str = "./cache",
                 json_file: str = "diseases_data.json",
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 num_workers: int = 4):
        """
        Khởi tạo với 3 cách tối ưu kết hợp
        
        Args:
            db_path: Đường dẫn Vector DB
            cache_path: Folder lưu cache metadata
            json_file: File JSON lưu dữ liệu (nhanh nhất)
            model_name: Model embedding
            num_workers: Số thread parallel read
        """
        self.db_path = db_path
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(exist_ok=True)
        
        self.json_file = Path(json_file)
        self.metadata_file = self.cache_path / "metadata.json"
        
        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="diseases",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.num_workers = num_workers
        
        print(f"✅ Initialized Combined Indexer")
        print(f"   - Vector DB: {db_path}")
        print(f"   - JSON Cache: {json_file}")
        print(f"   - Metadata: {self.metadata_file}")
        print(f"   - Workers: {num_workers}")
    
    # ============ CÁCH 1: Parallel Read ============
    def _read_disease_folder(self, disease_folder: Path) -> tuple:
        """
        Đọc 1 folder bệnh (chạy parallel)
        """
        disease_name = disease_folder.name
        files = {}
        
        for txt_file in disease_folder.glob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        files[txt_file.stem] = content
            except Exception as e:
                print(f"⚠️  Error {txt_file}: {e}")
        
        return disease_name, files
    
    def load_diseases_parallel(self, root_folder: str) -> dict:
        """
        Cách 1: Parallel read từ folders (10-20 giây)
        """
        root_path = Path(root_folder)
        disease_folders = sorted([d for d in root_path.iterdir() if d.is_dir()])
        
        print(f"\n📂 [Cách 1] Parallel reading {len(disease_folders)} diseases...")
        print(f"   Using {self.num_workers} workers...")
        
        diseases = {}
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            results = executor.map(self._read_disease_folder, disease_folders)
            
            for idx, (disease_name, files) in enumerate(results, 1):
                diseases[disease_name] = files
                if idx % 10 == 0 or idx == 1:
                    print(f"   [{idx}/{len(disease_folders)}] ✅ {disease_name}")
        
        print(f"✅ Parallel read completed! Total: {len(diseases)} diseases")
        return diseases
    
    # ============ CÁCH 2: JSON Cache ============
    def get_folder_hash(self, root_folder: str) -> str:
        """
        Tính hash folder để detect thay đổi
        """
        hash_obj = hashlib.md5()
        
        for file_path in sorted(Path(root_folder).rglob("*.txt")):
            try:
                with open(file_path, 'rb') as f:
                    hash_obj.update(f.read())
            except:
                pass
        
        return hash_obj.hexdigest()
    
    def is_json_cache_valid(self, root_folder: str) -> bool:
        """
        Kiểm tra JSON cache có hợp lệ không
        """
        # Kiểm tra file JSON tồn tại
        if not self.json_file.exists():
            print("📭 JSON file not found")
            return False
        
        # Kiểm tra metadata
        if not self.metadata_file.exists():
            print("📭 Metadata not found")
            return False
        
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            current_hash = self.get_folder_hash(root_folder)
            
            if metadata.get('folder_hash') == current_hash:
                print(f"✅ Cache valid! (hash match)")
                return True
            else:
                print("❌ Cache invalid (hash mismatch - data changed)")
                return False
        except Exception as e:
            print(f"❌ Cache error: {e}")
            return False
    
    def load_from_json(self) -> dict:
        """
        Cách 2a: Load từ JSON cache (1-2 giây)
        """
        print(f"\n⚡ [Cách 2a] Loading from JSON cache...")
        
        with open(self.json_file, 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        
        print(f"✅ Loaded {len(diseases)} diseases from JSON (⚡ super fast!)")
        return diseases
    
    def save_to_json(self, diseases: dict, root_folder: str):
        """
        Cách 2b: Save vào JSON (1-2 giây)
        """
        print(f"\n💾 [Cách 2b] Saving to JSON cache...")
        
        # Lưu JSON
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(diseases, f, ensure_ascii=False, indent=2)
        
        # Lưu metadata
        metadata = {
            'folder_hash': self.get_folder_hash(root_folder),
            'saved_at': datetime.now().isoformat(),
            'total_diseases': len(diseases),
            'json_file': str(self.json_file)
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Saved {len(diseases)} diseases to JSON")
        print(f"   📄 File size: {self.json_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # ============ CÁCH 3: Smart Load (Tự động chọn cách tốt nhất) ============
    def load_diseases_smart(self, root_folder: str) -> dict:
        """
        Cách 3: Load thông minh (tự động chọn cách tốt nhất)
        
        Logic:
        - Nếu JSON cache hợp lệ → Load từ JSON (⚡ 1-2s)
        - Nếu JSON cache không hợp lệ → Parallel read (📂 10-20s) → Save JSON
        """
        print("\n" + "="*60)
        print("🎯 [Cách 3] SMART LOAD - Tự động chọn cách tốt nhất")
        print("="*60)
        
        # Kiểm tra JSON cache
        if self.is_json_cache_valid(root_folder):
            # ✅ Cache hợp lệ → Load từ JSON (nhanh nhất)
            print("\n🚀 Strategy: Load from JSON cache")
            diseases = self.load_from_json()
            return diseases
        else:
            # ❌ Cache không hợp lệ → Parallel read + Save JSON
            print("\n🚀 Strategy: Parallel read + Save JSON")
            
            # Step 1: Parallel read
            diseases = self.load_diseases_parallel(root_folder)
            
            # Step 2: Save JSON
            self.save_to_json(diseases, root_folder)
            
            return diseases
    
    # ============ Chunking ============
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list:
        """Chia text thành chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.7:
                    end = start + last_period + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return [c for c in chunks if len(c.strip()) > 50]
    
    # ============ Indexing ============
    def index_diseases(self, diseases: dict):
        """
        Index diseases vào Vector DB
        """
        print(f"\n🔄 Indexing {len(diseases)} diseases to Vector DB...")
        
        total_chunks = 0
        total_diseases = len(diseases)
        
        for disease_idx, (disease_name, files) in enumerate(diseases.items(), 1):
            if disease_idx % 10 == 0 or disease_idx == 1:
                print(f"   [{disease_idx}/{total_diseases}] Indexing: {disease_name}")
            
            for file_name, content in files.items():
                chunks = self.chunk_text(content)
                
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_id = f"{disease_name}_{file_name}_{chunk_idx}"
                    
                    metadata = {
                        "disease": disease_name,
                        "file": file_name,
                        "chunk_idx": chunk_idx,
                        "indexed_at": datetime.now().isoformat()
                    }
                    
                    self.collection.add(
                        ids=[chunk_id],
                        documents=[chunk],
                        metadatas=[metadata]
                    )
                    
                    total_chunks += 1
        
        print(f"✅ Indexed {total_chunks} chunks to Vector DB")
        return total_chunks
    
    def get_stats(self) -> dict:
        """Lấy thống kê"""
        results = self.collection.get()
        diseases = {}
        
        for metadata in results['metadatas']:
            disease = metadata.get('disease')
            if disease not in diseases:
                diseases[disease] = 0
            diseases[disease] += 1
        
        return {
            'total_chunks': len(results['ids']),
            'total_diseases': len(diseases),
            'json_file_size_mb': self.json_file.stat().st_size / 1024 / 1024 if self.json_file.exists() else 0
        }


# ============ MAIN ============
if __name__ == "__main__":
    DISEASES_FOLDER = r"C:\Dự án\Medplot\medpilot_remind\DermNet_Data_Vietnamese"
    DB_PATH = "./chroma_db"
    JSON_FILE = "diseases_data.json"
    
    print("\n" + "="*60)
    print("🚀 DISEASE INDEXER - 3 OPTIMIZATIONS COMBINED")
    print("="*60)
    
    # Khởi tạo
    indexer = DiseaseIndexerCombined(
        db_path=DB_PATH,
        json_file=JSON_FILE,
        num_workers=4  # 4 threads parallel
    )
    
    # Load thông minh (tự động chọn cách tốt nhất)
    diseases = indexer.load_diseases_smart(DISEASES_FOLDER)
    
    # Index vào Vector DB
    indexer.index_diseases(diseases)
    
    # Hiển thị thống kê
    print("\n" + "="*60)
    print("📊 STATISTICS")
    print("="*60)
    stats = indexer.get_stats()
    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Total Diseases: {stats['total_diseases']}")
    print(f"JSON File Size: {stats['json_file_size_mb']:.2f} MB")
    
    print("\n✨ ALL DONE! Ready for RAG queries")