import os
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime

class DiseaseIndexer:
    def __init__(self, db_path: str = "./chroma_db", model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Khởi tạo Disease Indexer
        
        Args:
            db_path: Đường dẫn lưu Chroma DB
            model_name: Tên model Sentence-Transformers (hỗ trợ tiếng Việt)
        """
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        
        # Khởi tạo Chroma client (local persistent)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="diseases",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"✅ Model loaded: {model_name}")
        print(f"✅ Vector DB initialized at: {db_path}")
    
    def load_diseases_from_folder(self, root_folder: str) -> dict:
        """
        Load tất cả bệnh từ thư mục root
        
        Args:
            root_folder: Đường dẫn thư mục DermNet_Data_Vietnamese
        
        Returns:
            Dict[disease_name] = Dict[file_content]
        """
        diseases = {}
        root_path = Path(root_folder)
        
        if not root_path.exists():
            print(f"❌ Folder không tồn tại: {root_folder}")
            return diseases
        
        # Duyệt tất cả thư mục con (mỗi bệnh là 1 folder)
        for disease_folder in sorted(root_path.iterdir()):
            if not disease_folder.is_dir():
                continue
            
            disease_name = disease_folder.name
            diseases[disease_name] = {}
            
            # Đọc tất cả file .txt trong folder bệnh
            for txt_file in disease_folder.glob("*.txt"):
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:  # Chỉ lưu file không rỗng
                            file_name = txt_file.stem
                            diseases[disease_name][file_name] = content
                except Exception as e:
                    print(f"⚠️  Lỗi đọc file {txt_file}: {e}")
        
        print(f"✅ Loaded {len(diseases)} diseases")
        return diseases
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list:
        """
        Chia text thành các chunk nhỏ hơn
        
        Args:
            text: Text cần chia
            chunk_size: Số ký tự mỗi chunk
            overlap: Số ký tự overlap giữa chunks
        
        Returns:
            List các chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Tìm điểm dừng hợp lý (cuối câu)
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.7:  # Nếu có dấu chấm
                    end = start + last_period + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return [c for c in chunks if len(c.strip()) > 50]  # Loại chunks quá ngắn
    
    def index_diseases(self, diseases: dict):
        """
        Index tất cả bệnh vào Vector DB
        
        Args:
            diseases: Dict chứa toàn bộ dữ liệu bệnh
        """
        total_chunks = 0
        
        for disease_name, files in diseases.items():
            print(f"\n📌 Indexing: {disease_name}")
            
            for file_name, content in files.items():
                # Chia thành chunks
                chunks = self.chunk_text(content)
                
                for chunk_idx, chunk in enumerate(chunks):
                    # Tạo ID duy nhất
                    chunk_id = f"{disease_name}_{file_name}_{chunk_idx}"
                    
                    # Tạo metadata
                    metadata = {
                        "disease": disease_name,
                        "file": file_name,
                        "chunk_idx": chunk_idx,
                        "indexed_at": datetime.now().isoformat()
                    }
                    
                    # Thêm vào collection
                    self.collection.add(
                        ids=[chunk_id],
                        documents=[chunk],
                        metadatas=[metadata]
                    )
                    
                    total_chunks += 1
        
        print(f"\n✅ Indexed {total_chunks} chunks successfully!")
        return total_chunks
    
    def get_collection_stats(self):
        """Lấy thống kê về collection"""
        count = self.collection.count()
        print(f"📊 Total chunks in DB: {count}")
        return count

# ============ MAIN ============
if __name__ == "__main__":
    # Đường dẫn tới thư mục DermNet_Data_Vietnamese
    DISEASES_FOLDER = "C:\Dự án\Medplot\medpilot_remind\DermNet_Data_Vietnamese"  # ⚠️ Thay đường dẫn thực tế của bạn
    DB_PATH = "./chroma_db"
    
    # Khởi tạo indexer
    indexer = DiseaseIndexer(db_path=DB_PATH)
    
    # Load dữ liệu từ folders
    print("\n🔍 Loading diseases from folders...")
    diseases = indexer.load_diseases_from_folder(DISEASES_FOLDER)
    
    # Index vào Vector DB
    print("\n🚀 Starting indexing...")
    indexer.index_diseases(diseases)
    
    # Hiển thị thống kê
    indexer.get_collection_stats()
    
    print("\n✨ Done! Vector DB ready for RAG queries")