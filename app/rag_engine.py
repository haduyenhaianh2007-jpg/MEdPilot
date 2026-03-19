"""
RAG Engine - Adapt cho JSON files
Load từ diseases.json → Embedding → Vector DB
⚡ MEMORY OPTIMIZED: Lazy loading + batch processing
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import gc

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG Engine cho JSON files - Memory Optimized"""

    def __init__(self,
                 diseases_json: str,
                 db_path: str,
                 embedding_model: str,
                 top_k: int = 3,
                 cache_size: int = 1000):
        """
        Khởi tạo RAG Engine
        
        Args:
            diseases_json: Path tới diseases.json
            db_path: Path lưu Vector DB
            embedding_model: Model tạo embeddings
            top_k: Số documents retrieve
            cache_size: Embedding cache size (tối ưu tốc độ)
        """
        self.diseases_json = diseases_json
        self.db_path = db_path
        self.top_k = top_k
        self.diseases_cached = None  # Lazy load diseases
        self.indexed = False  # Track if DB is indexed
        
        # ⚡ Embedding cache để avoid re-computing
        self.embedding_cache = {}
        self.cache_size = cache_size

        logger.info(f"📥 Loading embedding model... (cache size: {cache_size})")
        self.embedding_model = SentenceTransformer(embedding_model)

        logger.info(f"💾 Initializing Chroma DB...")
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="medical_diseases",
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"✅ RAG Engine initialized\n")

    def load_diseases_from_json(self) -> Dict[str, Dict]:
        """
        Load bệnh từ diseases.json
        
        Format JSON:
        {
            "Bệnh gai den": {
                "content": "...",
                "source": "bệnh gai den.txt",
                "length": 1234
            },
            ...
        }
        """
        logger.info(f"📂 Loading diseases from {self.diseases_json}")

        # Kiểm tra file tồn tại
        if not Path(self.diseases_json).exists():
            logger.error(f"❌ File not found: {self.diseases_json}")
            logger.info(f"   Run: python convert_text_to_json.py")
            return {}

        try:
            # Đọc JSON
            with open(self.diseases_json, 'r', encoding='utf-8') as f:
                diseases = json.load(f)

            logger.info(f"📋 Found {len(diseases)} diseases")

            # Thống kê
            total_chars = sum(d.get("length", 0) for d in diseases.values())
            logger.info(f"📊 Total characters: {total_chars:,}\n")

            return diseases

        except Exception as e:
            logger.error(f"❌ Error loading JSON: {str(e)}")
            return {}

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Chia text thành chunks"""
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Chia tại dấu chấm nếu có
            if end < len(text):
                last_period = text.rfind('.', start, end)
                if last_period > start + chunk_size * 0.7:
                    end = last_period + 1

            chunk = text[start:end].strip()

            if len(chunk) > 50:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    def index_diseases(self, diseases: Dict, force_reindex: bool = False, batch_size: int = 50) -> int:
        """Index bệnh vào Vector DB - sử dụng batch processing để tối ưu tốc độ"""
        
        if force_reindex:
            logger.warning("🔄 Force reindex...")
            try:
                self.chroma_client.delete_collection(name="medical_diseases")
                self.collection = self.chroma_client.get_or_create_collection(
                    name="medical_diseases",
                    metadata={"hnsw:space": "cosine"}
                )
            except:
                pass

        logger.info(f"📊 Indexing {len(diseases)} diseases with batch_size={batch_size}\n")

        total_chunks = 0
        batch_ids = []
        batch_embeddings = []
        batch_documents = []
        batch_metadatas = []
        batch_timestamp = datetime.now().isoformat()

        disease_items = list(diseases.items())

        for disease_idx, (disease_name, disease_info) in enumerate(disease_items, 1):
            # Log progress every 20 diseases
            if disease_idx % 20 == 1 or disease_idx == len(diseases):
                logger.info(f"[{disease_idx}/{len(diseases)}] {disease_name}...")

            # Lấy content từ JSON - combine tất cả sections
            content = "\n\n".join([
                f"{section_name}: {section_content}"
                for section_name, section_content in disease_info.items()
                if isinstance(section_content, str) and section_content.strip()
            ])

            if not content or len(content) < 50:
                continue

            # Chunk text
            chunks = self.chunk_text(content)

            for chunk_idx, chunk in enumerate(chunks):
                # ID duy nhất
                chunk_id = f"{disease_name}_{chunk_idx}"

                # Embed (sentence-transformers is efficient)
                embedding = self.embedding_model.encode(chunk)

                # Metadata
                metadata = {
                    "disease": disease_name,
                    "chunk_idx": chunk_idx,
                    "indexed_at": batch_timestamp
                }

                # Batch accumulation
                batch_ids.append(chunk_id)
                batch_embeddings.append(embedding.tolist())
                batch_documents.append(chunk)
                batch_metadatas.append(metadata)
                total_chunks += 1

                # Add batch to Chroma when size reached
                if len(batch_ids) >= batch_size:
                    self.collection.add(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                    batch_ids, batch_embeddings, batch_documents, batch_metadatas = [], [], [], []

        # Add remaining batch
        if batch_ids:
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas
            )

        logger.info(f"✅ Total chunks indexed: {total_chunks}\n")
        return total_chunks

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Lấy chunks relevant từ Vector DB - ⚡ With embedding cache"""
        
        # Lazy index on first query
        if not self.indexed:
            logger.info("🔄 First query - indexing diseases...")
            if not self.diseases_cached:
                self.diseases_cached = self.load_diseases_from_json()
            if self.diseases_cached:
                self.index_diseases(self.diseases_cached)
                self.indexed = True
        
        if top_k is None:
            top_k = self.top_k

        # ⚡ Check cache first
        if query in self.embedding_cache:
            query_embedding = self.embedding_cache[query]
            logger.debug(f"📦 Cache hit for: '{query[:50]}...'")
        else:
            # Embed query
            query_embedding = self.embedding_model.encode(query)
            
            # Store in cache (FIFO eviction if full)
            if len(self.embedding_cache) >= self.cache_size:
                oldest_key = next(iter(self.embedding_cache))
                del self.embedding_cache[oldest_key]
            
            self.embedding_cache[query] = query_embedding

        # Search in Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        retrieved = []

        if results['ids'] and len(results['ids']) > 0:
            for idx in range(len(results['ids'][0])):
                retrieved.append({
                    'disease': results['metadatas'][0][idx]['disease'],
                    'content': results['documents'][0][idx],
                    'distance': results['distances'][0][idx]
                })

        return retrieved

    def get_count(self) -> int:
        """Lấy số chunks"""
        return self.collection.count()