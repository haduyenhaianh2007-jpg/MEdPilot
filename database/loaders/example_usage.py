from load_and_index_diseases import DiseaseIndexer
from rag_retriever import DiseaseRAGRetriever

# ============ BƯỚC 1: INDEX DỮ LIỆU (LẦN ĐẦU) ============
print("="*60)
print("BƯỚC 1: INDEX DỮ LIỆU TỚI VECTOR DB")
print("="*60)

indexer = DiseaseIndexer(db_path="./chroma_db")
diseases = indexer.load_diseases_from_folder(r"C:\Dự án\Medplot\medpilot_remind\DermNet_Data_Vietnamese")  # ⚠️ Thay đường dẫn
indexer.index_diseases(diseases)

# ============ BƯỚC 2: QUERY DỮ LIỆU ============
print("\n" + "="*60)
print("BƯỚC 2: QUERY THÔNG TIN VỀ BỆNH")
print("="*60)

retriever = DiseaseRAGRetriever(db_path="./chroma_db")

# Query 1: Tìm kiếm thông tin về 1 triệu chứng
print("\n📌 Query 1: Tìm triệu chứng của bệnh gai den")
query1 = "Bệnh gai den có những triệu chứng gì?"
results = retriever.retrieve(query1, top_k=3)

for result in results:
    print(f"\n✅ Rank {result['rank']} (Similarity: {result['similarity']})")
    print(f"   🏥 Bệnh: {result['disease']}")
    print(f"   📄 Tài liệu: {result['file']}")
    print(f"   📝 Nội dung: {result['content'][:200]}...")

# Query 2: Tìm kiếm cách điều trị
print("\n\n📌 Query 2: Cách điều trị các bệnh da")
query2 = "Điều trị bệnh da liễu như thế nào?"
results = retriever.retrieve(query2, top_k=3)

for result in results:
    print(f"\n✅ Rank {result['rank']} (Similarity: {result['similarity']})")
    print(f"   🏥 Bệnh: {result['disease']}")
    print(f"   📄 Tài liệu: {result['file']}")
    print(f"   📝 Nội dung: {result['content'][:200]}...")

# Query 3: Lấy tất cả thông tin 1 bệnh
print("\n\n📌 Query 3: Lấy TẤT CẢ thông tin về bệnh 'Acanthosis nigricans'")
results = retriever.retrieve_by_disease("Acanthosis nigricans")
print(f"Tìm thấy {len(results)} chunks về bệnh này:")
for result in results:
    print(f"   - {result['file']}: {result['content'][:100]}...")

# Query 4: Liệt kê tất cả bệnh
print("\n\n📌 Query 4: Danh sách tất cả bệnh trong DB")
diseases_list = retriever.list_all_diseases()
print(f"Tổng cộng: {len(diseases_list)} bệnh")
print("Danh sách (10 bệnh đầu):")
for i, disease in enumerate(diseases_list[:10], 1):
    print(f"   {i}. {disease}")

# Query 5: Thống kê collection
print("\n\n📌 Query 5: Thống kê")
info = retriever.get_collection_info()
print(f"📊 Tổng chunks: {info['total_chunks']}")
print(f"📊 Tổng bệnh: {info['total_diseases']}")