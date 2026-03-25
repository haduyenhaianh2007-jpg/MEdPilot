
import os
import shutil
import sys
from pathlib import Path

# Add app directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.rag_engine import RAGEngine

def reset_database():
    db_path = settings.DB_PATH
    print(f"🧹 Resetting ChromaDB at: {db_path}")
    
    # 1. Delete the directory if it exists
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
            print(f"✅ Deleted existing database directory.")
        except Exception as e:
            print(f"❌ Could not delete directory: {e}")
            print("   Make sure the backend server (uvicorn) is STOPPED before running this script.")
            return

    # 2. Re-initialize RAG Engine (this will recreate the directory)
    print("⏳ Initializing RAGEngine and re-indexing...")
    try:
        engine = RAGEngine(
            diseases_json=settings.DISEASES_JSON,
            db_path=db_path,
            embedding_model=settings.EMBEDDING_MODEL
        )
        
        # 3. Load and Index
        diseases = engine.load_diseases_from_json()
        if not diseases:
            print("❌ No diseases found to index. check database/data/diseases_data.json")
            return
            
        count = engine.index_diseases(diseases, force_reindex=True)
        print(f"🚀 Successfully re-indexed {count} chunks across {len(diseases)} diseases!")
        
    except Exception as e:
        print(f"❌ Failed to reset/index: {e}")

if __name__ == "__main__":
    reset_database()
