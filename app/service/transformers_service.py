"""
Local Transformers LLM Service - Load model truc tiep
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
from typing import Dict, List
import time

logger = logging.getLogger(__name__)


class TransformersService:
    """Local LLM Service - Dung transformers"""

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
        device: str = "auto",
        load_in_4bit: bool = False,
        max_tokens: int = 2048
    ):
        """
        Khoi tao local LLM

        Args:
            model_name: Ten model tren HuggingFace
            device: 'cuda', 'cpu', 'auto'
            load_in_4bit: Neu co GPU, load 4bit de tiet kiem RAM
            max_tokens: So token toi da
        """
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.model = None
        self.tokenizer = None
        self.device = None
        
        logger.info(f"[Transformers] Bat dau tai model: {model_name}")
        logger.info(f"[Transformers] Device: {device}")
        
        # Kiem tra GPU
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"[Transformers] Su dung device: {self.device}")
        
        # Load model
        self._load_model(load_in_4bit)

    def _load_model(self, load_in_4bit: bool):
        """Tai model va tokenizer"""
        logger.info("[Transformers] Dang tai tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        logger.info("[Transformers] Dang tai model...")
        if load_in_4bit and self.device == "cuda":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                quantization_config=quantization_config
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            ).to(self.device)
        
        self.model.eval()
        
        logger.info(f"[Transformers] Model tai xong!")

    def query(
        self,
        messages: List[Dict],
        max_tokens: int = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Sinh response tu local model

        Args:
            messages: Danh sach tin nhan
            max_tokens: So token toi da
            temperature: Nhiet do sinh

        Returns:
            {success, answer, error, latency, method}
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
            
        logger.info(f"[Transformers] Query (max_tokens: {max_tokens})")
        start_time = time.time()
        
        try:
            # Chuyen doi messages thanh text
            prompt = self._format_messages(messages)
            
            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                add_generation_prompt=True
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    do_sample=temperature > 0
                )
            
            # Decode
            response_text = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[-1]:],
                skip_special_tokens=True
            )
            
            latency = time.time() - start_time
            logger.info(f"[Transformers] Thanh cong ({latency:.2f}s)")
            
            return {
                "success": True,
                "answer": response_text,
                "error": None,
                "latency": latency,
                "method": "transformers"
            }
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"[Transformers] Loi: {str(e)}")
            
            return {
                "success": False,
                "answer": f"Loi: {str(e)}",
                "error": str(e),
                "latency": latency,
                "method": "transformers"
            }

    def _format_messages(self, messages: List[Dict]) -> str:
        """Chuyen doi messages thanh prompt"""
        # Thu try chat template
        try:
            # Cho model co chat template
            formatted = self.tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=False
            )
            return formatted
        except:
            # Fallback - noi thu cong
            prompt = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n\n"
            
            prompt += "Assistant: "
            return prompt
