
import sys
import os
from pathlib import Path

# Add app directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.service.speech_extraction_service import SpeechExtractionService

def test_rules():
    service = SpeechExtractionService()
    
    test_cases = [
        {
            "name": "Contact Dermatitis Case (Hand + Detergent)",
            "data": {
                "lesion_location": ["hai bàn tay", "mu bàn tay"],
                "related_factors": ["nước rửa chén", "giặt đồ"],
                "medical_history": [],
                "main_symptoms": ["ngứa", "đỏ"],
                "onset_time": "2 tuần"
            }
        },
        {
            "name": "Atopic Flare Case",
            "data": {
                "lesion_location": ["khuỷu tay"],
                "related_factors": [],
                "medical_history": ["viêm da cơ địa"],
                "main_symptoms": ["ngứa", "khô da"],
            }
        },
        {
            "name": "Red Flag Case (Fever + Rapid Spread)",
            "data": {
                "lesion_location": ["chân"],
                "main_symptoms": ["sốt", "đau", "đỏ"],
                "onset_time": "lan nhanh từ sáng nay",
                "related_factors": []
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n--- Testing: {case['name']} ---")
        result = service._apply_clinical_logic(case['data'])
        
        print(f"Considerations: {result.get('possible_considerations')}")
        print(f"Red Flags: {result.get('red_flags')}")
        print(f"Questions: {result.get('questions_to_ask')}")
        print(f"Alert Level: {result.get('alert_level')}")

if __name__ == "__main__":
    test_rules()
