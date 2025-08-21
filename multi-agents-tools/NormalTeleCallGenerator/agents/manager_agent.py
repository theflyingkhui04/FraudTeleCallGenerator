from typing import List, Dict, Any, Tuple, Optional
from .base_agent import BaseAgent
from .prompts.manager_prompts import MANAGER_SYSTEM_PROMPT
import config
import json
import time
import logging

class ManagerAgent(BaseAgent):
    """Agent quản lý, đánh giá hội thoại và quyết định có nên kết thúc hay không"""
    
    def __init__(self, model: Optional[str] = None, strictness: str = "medium", 
                 api_key: Optional[str] = None, retry_delay: float = 5):
        super().__init__(role="manager", model=model or config.DEFAULT_MODEL, 
                        api_key=api_key)
        self.strictness = strictness  # low, medium, high
        self.retry_delay = retry_delay
        
    def get_system_prompt(self) -> str:
        """Lấy prompt hệ thống đã được tuỳ biến"""
        return MANAGER_SYSTEM_PROMPT.format(strictness=self.strictness)
    
    def generate_response(self, message: str) -> str:
        """Base implementation - not used in manager"""
        return ""
    
    def evaluate_dialogue(self, dialogue_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Đánh giá hội thoại và trả về quyết định kết thúc, ai là người kết thúc và lý do"""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Xây dựng lịch sử hội thoại đầy đủ
        dialogue_text = "\n".join([
            f"{'Kẻ lừa đảo' if msg['role'] == 'left' else 'Người dùng'}: {msg['content']}"
            for msg in dialogue_history
        ])
        
        # Sử dụng đoạn hội thoại đã xây dựng
        messages.append({
            "role": "user", 
            "content": f"Hãy đánh giá đoạn hội thoại sau và quyết định có nên kết thúc không, ai là người nên kết thúc:\n\n{dialogue_text}\n\nVui lòng trả lời bằng định dạng JSON, gồm các trường sau:\n- should_terminate: giá trị True/False, cho biết có nên kết thúc không\n- terminator: chuỗi, giá trị có thể là 'left' (kẻ lừa đảo kết thúc), 'right' (người dùng kết thúc), 'natural' (kết thúc tự nhiên) hoặc 'endcall' (gác máy)\n- reason: chuỗi, giải thích chi tiết lý do kết thúc hoặc tiếp tục"
        })
        
        # Thêm logic retry
        retry_count = 0
        while True:
            try:
                # Gọi API để sinh phản hồi
                reply = self.client.chat_completion(
                    messages=messages,
                    model=self.model or config.DEFAULT_MODEL,
                    temperature=0.3,
                    max_tokens=500
                )
                
                # Kiểm tra lỗi API
                if reply and "API" in reply:
                    retry_count += 1
                    if retry_count <= 3:
                        logging.warning(f"API error, retrying ({retry_count}/3): {reply}")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        logging.error(f"API error after 3 retries: {reply}")
                        return {"should_terminate": True, "terminator": "manager", "reason": f"Lỗi API: {reply}"}
                
                # Thử parse JSON
                try:
                    # Tìm JSON trong phản hồi
                    json_match = self._extract_json(reply or "")
                    if json_match:
                        result = json.loads(json_match)
                    else:
                        # Nếu không tìm thấy JSON, thử parse toàn bộ reply
                        result = json.loads(reply or "{}")
                        
                    # Kiểm tra các trường bắt buộc
                    if "should_terminate" in result and "terminator" in result and "reason" in result:
                        # Chuyển đổi các giá trị thành định dạng chuẩn
                        result["should_terminate"] = bool(result["should_terminate"])
                        result["terminator"] = str(result["terminator"])
                        result["reason"] = str(result["reason"])
                        
                        return result
                    else:
                        # Thiếu trường bắt buộc, thử phân tích dạng text
                        return self._fallback_text_analysis(reply or "")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    # Nếu không parse được JSON, thử phân tích dạng text
                    return self._fallback_text_analysis(reply or "")
                    
            except Exception as e:
                retry_count += 1
                if retry_count <= 3:
                    logging.warning(f"Manager agent error, retrying ({retry_count}/3): {e}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logging.error(f"Manager agent error after 3 retries: {e}")
                    return {"should_terminate": True, "terminator": "manager", "reason": f"Lỗi hệ thống: {str(e)}"}
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Trích xuất chuỗi JSON từ text"""
        import re
        # Tìm pattern JSON
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            return match.group(0)
        return None
    
    def _fallback_text_analysis(self, reply: str) -> Dict[str, Any]:
        """Phân tích text khi không parse được JSON"""
        reply_lower = reply.lower()
        
        # Phát hiện từ khoá kết thúc
        terminate_keywords = ["kết thúc", "gác máy", "end", "terminate", "stop", "bye", "goodbye"]
        should_terminate = any(keyword in reply_lower for keyword in terminate_keywords)
        
        # Phát hiện ai là người kết thúc
        if "người dùng" in reply_lower or "right" in reply_lower:
            terminator = "right"
        elif "kẻ lừa đảo" in reply_lower or "left" in reply_lower:
            terminator = "left"
        else:
            terminator = "natural"
        
        return {
            "should_terminate": should_terminate,
            "terminator": terminator,
            "reason": reply[:100] + "..." if len(reply) > 100 else reply
        }
