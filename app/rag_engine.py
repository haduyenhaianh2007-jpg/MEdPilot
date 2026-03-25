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
                 cache_size: int = 500):
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

    def chunk_text(self, text: str, chunk_size: int = 500, min_chunk_size: int = 100) -> List[str]:
        """
        Chia text thanh chunks nho - SAFE, khong co overlap de tranh infinite loop.
        start luon tien ve phia truoc (= end), co max_iterations safety limit.
        """
        chunks = []
        start = 0
        text_len = len(text)
        # Safety: so vong lap toi da bang so lan co the chia (khong bao gio loop vo han)
        max_iterations = (text_len // min_chunk_size) + 10
        iterations = 0

        while start < text_len and iterations < max_iterations:
            iterations += 1
            end = min(start + chunk_size, text_len)

            # Tim diem ngat tu nhien gan nhat (dau cham / xuong dong)
            if end < text_len:
                for sep in ['.', '\n', ' ']:
                    pos = text.rfind(sep, start, end)
                    if pos > start + min_chunk_size:
                        end = pos + 1
                        break

            chunk = text[start:end].strip()
            if len(chunk) >= min_chunk_size:
                chunks.append(chunk)

            # LUON tien ve phia truoc - khong bao gio lui
            start = end

        return chunks

    def index_diseases(self, diseases: Dict, force_reindex: bool = False, batch_size: int = 16,
                       max_chunks_per_disease: int = 100) -> int:
        """Index benh vao Vector DB - chunk nho, encode va add lien tuc.
        max_chunks_per_disease: gioi han so chunks moi benh, tranh RAM explosion.
        """
        if force_reindex:
            logger.warning("Force reindex...")
            try:
                self.chroma_client.delete_collection(name="medical_diseases")
                self.collection = self.chroma_client.get_or_create_collection(
                    name="medical_diseases",
                    metadata={"hnsw:space": "cosine"}
                )
            except:
                pass

        logger.info(f"Indexing {len(diseases)} diseases (batch_size={batch_size}, max_chunks={max_chunks_per_disease})")

        total_chunks = 0
        batch_timestamp = datetime.now().isoformat()
        disease_items = list(diseases.items())

        for disease_idx, (disease_name, disease_info) in enumerate(disease_items, 1):
            if disease_idx % 20 == 0:
                logger.info(f"[{disease_idx}/{len(diseases)}] {disease_name}... ({total_chunks} chunks)")

            content = "\n\n".join([
                f"{section_name}: {section_content}"
                for section_name, section_content in disease_info.items()
                if isinstance(section_content, str) and section_content.strip()
            ])

            if not content or len(content) < 50:
                continue

            chunks = self.chunk_text(content)[:max_chunks_per_disease]  # Safety cap

            # Process each chunk
            batch_ids = []
            batch_embeddings = []
            batch_documents = []
            batch_metadatas = []

            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = f"{disease_name}_{chunk_idx}"
                
                metadata = {
                    "disease": disease_name,
                    "chunk_idx": chunk_idx,
                    "indexed_at": batch_timestamp
                }

                batch_ids.append(chunk_id)
                batch_documents.append(chunk)
                batch_metadatas.append(metadata)

                # Encode when batch is full
                if len(batch_ids) >= batch_size:
                    embeddings = self.embedding_model.encode(batch_documents)
                    batch_embeddings = embeddings.tolist()
                    
                    self.collection.add(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                    
                    total_chunks += len(batch_ids)
                    batch_ids, batch_embeddings, batch_documents, batch_metadatas = [], [], [], []

            # Add remaining chunks
            if batch_ids:
                embeddings = self.embedding_model.encode(batch_documents)
                batch_embeddings = embeddings.tolist()
                
                self.collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                total_chunks += len(batch_ids)

        logger.info(f"Total chunks indexed: {total_chunks}")
        return total_chunks

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Lấy chunks relevant từ Vector DB - ⚡ With embedding cache"""
        
        # Lazy index on first query - skip if DB already has data
        if not self.indexed:
            existing_count = self.get_count()
            if existing_count > 0:
                logger.info(f"✅ ChromaDB has {existing_count} chunks - skipping re-indexing (0.1s)")
                self.indexed = True
            else:
                logger.info("🔄 ChromaDB empty - indexing diseases...")
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
            
            # Store in cache (FIFO eviction khi day - gioi han max 500 entries)
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