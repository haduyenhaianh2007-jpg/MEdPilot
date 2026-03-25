"""
Script index diseases vao ChromaDB
Chay truoc khi start backend
"""

import json
import os
from pathlib import Path

# Add app to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag_engine import RAGEngine
from app.config import settings

def main():
    print("=" * 60)
    print("INDEXING DISEASES TO CHROMADB")
    print("=" * 60)
    
    # Check JSON file
    json_path = settings.DISEASES_JSON
    print(f"\n1. Loading diseases from: {json_path}")
    
    if not os.path.exists(json_path):
        print(f"[ERROR] File not found: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        diseases = json.load(f)
    
    print(f"[OK] Found {len(diseases)} diseases")
    
    # Init RAG Engine
    print(f"\n2. Initializing RAG Engine...")
    print(f"   Embedding model: {settings.EMBEDDING_MODEL}")
    print(f"   DB path: {settings.DB_PATH}")
    
    rag = RAGEngine(
        diseases_json=settings.DISEASES_JSON,
        db_path=settings.DB_PATH,
        embedding_model=settings.EMBEDDING_MODEL,
        top_k=settings.TOP_K,
        cache_size=settings.MODEL_CACHE_SIZE
    )
    
    # Check existing count
    try:
        existing_count = rag.get_count()
        print(f"\n3. Existing chunks in DB: {existing_count}")
    except:
        existing_count = 0
        print(f"\n3. No existing data")
    
    # Ask to reindex
    if existing_count > 0:
        print(f"\n[WARNING] Database already has {existing_count} chunks")
        response = input("Reindex? (y/N): ").strip().lower()
        if response != 'y':
            print("Skipped indexing.")
            return
    
    # Index
    print(f"\n4. Indexing diseases...")
    print("   (This may take a few minutes for the first time)")
    print("   Embedding model needs to be downloaded/loaded.")
    
    total_chunks = rag.index_diseases(diseases, force_reindex=True, batch_size=50)
    
    print(f"\n[OK] Indexing complete!")
    print(f"   Total chunks: {total_chunks}")
    print("=" * 60)


if __name__ == "__main__":
    main()
