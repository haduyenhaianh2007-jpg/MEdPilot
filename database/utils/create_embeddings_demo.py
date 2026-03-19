"""
Demo: Tạo embeddings từ JSON sử dụng Sentence-Transformers
"""

import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ============ LOAD JSON ============
print("📂 Loading diseases from JSON...")
with open("diseases_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"✅ Loaded {len(data)} diseases\n")

# ============ INIT MODEL ============
print("🤖 Loading embedding model...")
# paraphrase-multilingual-MiniLM-L12-v2: hỗ trợ tiếng Việt, 384 chiều
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print(f"✅ Model loaded\n")

# ============ ENCODE SAMPLES ============
print("🔄 Encoding samples...")

# Lấy 3 bệnh đầu tiên làm ví dụ
sample_diseases = list(data.items())[:3]

embeddings_dict = {}

for disease_name, disease_info in sample_diseases:
    content = disease_info.get("content", "")
    
    # Encode toàn bộ content thành 1 vector
    embedding = model.encode(content)
    embeddings_dict[disease_name] = embedding
    
    print(f"✅ {disease_name}")
    print(f"   Content length: {len(content)} chars")
    print(f"   Vector shape: {embedding.shape}")
    print(f"   First 5 values: {embedding[:5]}\n")

# ============ CHECK SIMILARITY ============
print("📊 Kiểm tra độ tương đồng (Cosine Similarity)")
print("="*60)

diseases_list = list(embeddings_dict.items())

if len(diseases_list) >= 2:
    disease1_name, embedding1 = diseases_list[0]
    disease2_name, embedding2 = diseases_list[1]
    
    # Tính cosine similarity
    similarity = cosine_similarity(
        [embedding1], 
        [embedding2]
    )[0][0]
    
    print(f"{disease1_name} vs {disease2_name}")
    print(f"Similarity: {similarity:.3f}")
    print(f"(1.0 = giống hệt, 0.0 = hoàn toàn khác)\n")

# ============ DEMO SEARCH ============
print("🔍 Demo tìm kiếm")
print("="*60)

# Query
query = "Bệnh gai đen có triệu chứng gì?"
query_embedding = model.encode(query)

print(f"Query: {query}\n")
print(f"Query vector shape: {query_embedding.shape}\n")

# So sánh với các bệnh
print("Top 3 bệnh phù hợp nhất:")
similarities = []

for disease_name, embedding in embeddings_dict.items():
    score = cosine_similarity([query_embedding], [embedding])[0][0]
    similarities.append((disease_name, score))

# Sắp xếp theo độ tương đồng
similarities.sort(key=lambda x: x[1], reverse=True)

for idx, (disease_name, score) in enumerate(similarities[:3], 1):
    print(f"{idx}. {disease_name}: {score:.3f}")

print("\n✨ Demo hoàn tất!")
print("Để tạo embeddings cho TẤT CẢ bệnh, xem load_and_index_optimized_combined.py")
