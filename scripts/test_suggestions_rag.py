
import requests
import json

def test_suggestions():
    url = "http://localhost:8000/api/v1/query?role=doctor"
    
    transcript = """
    Bác sĩ ơi, em bị nổi đỏ, ngứa nhiều, bong vảy nhẹ ở hai bàn tay khoảng hai tuần nay. 
    Lúc đầu khởi phát từ mu bàn tay rồi lan ra cổ tay. Cả hai bên đều bị nhưng mà tay phải bị nặng hơn. 
    Em cảm thấy không có cảm giác đau, không rõ có rát, không có mụn nước, không chảy dịch và không chảy máu. 
    Dạo gần đây, em hay rửa chén giúp mẹ và tiếp xúc nhiều với nước rửa chén. 
    Mỗi lần như vậy thì triệu chứng ngứa tăng lên. 
    Em trước khi đi khám có tự bôi kem mua ở tiệm thuốc gần nhà nhưng em không nhớ rõ tên. 
    Ban đầu đỡ ít, sau dần thì không khỏi. Trước đây em có tiền sử bị viêm da cơ địa khoảng 2 năm trước. 
    Dị ứng đặc biệt thì em chưa có. Em không sốt cũng không mệt.
    """
    
    payload = {
        "query": transcript,
        "user_role": "doctor"
    }
    
    print(f"Testing suggestions via {url}...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("\nAI Answer:")
            print(data.get("answer"))
            print(f"\nRetrieved chunks: {data.get('retrieved_chunks')}")
            print(f"Confidence: {data.get('confidence')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_suggestions()
