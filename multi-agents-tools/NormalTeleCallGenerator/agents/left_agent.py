from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from .prompts.left_prompts import LEFT_SYSTEM_PROMPT
import config
import time
import logging

class LeftAgent(BaseAgent):
    """Nhân viên dịch vụ, chịu trách nhiệm cung cấp dịch vụ và hỗ trợ khách hàng"""
    
    def __init__(self, model: Optional[str] = None, conversation_type: str = "Tư vấn dịch vụ khách hàng", 
                 api_key: Optional[str] = None, max_retries: int = 10, retry_delay: float = 5):
        super().__init__(
            role="left", 
            model=model or config.DEFAULT_MODEL, 
            api_key=api_key
        )
        self.conversation_type = conversation_type
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    def get_system_prompt(self) -> str:
        """Lấy prompt hệ thống đã tuỳ chỉnh"""
        return LEFT_SYSTEM_PROMPT.format(conversation_type=self.conversation_type)
    
    def generate_response(self, message: Optional[str] = None) -> str:
        """Tạo phản hồi dịch vụ, thêm cơ chế thử lại lỗi"""
        # Tin nhắn hoặc phản hồi ban đầu
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        # Thêm lịch sử trò chuyện
        for msg in self.conversation_history:
            messages.append(msg)
            
        # Nếu có tin nhắn mới, thêm vào danh sách tin nhắn
        if message:
            messages.append({"role": "user", "content": message})
        else:
            # Nếu không có message (lần đầu tiên), thêm message khởi đầu
            messages.append({"role": "user", "content": "Bắt đầu cuộc gọi tư vấn dịch vụ."})
        
        # Thêm logic retry khi gọi API
        retry_count = 0
        while True:
            try:
                # Gọi API để sinh phản hồi (Gemini)
                reply = self.client.chat_completion(messages=messages)
                
                # Kiểm tra phản hồi hợp lệ
                if reply and len(reply.strip()) > 0:
                    # Cập nhật lịch sử trò chuyện
                    if message:
                        self.update_history("user", message)
                    self.update_history("assistant", reply)
                    return reply
                else:
                    # Phản hồi rỗng hoặc không hợp lệ
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        logging.warning(f"API request thất bại (lần thử {retry_count}): Phản hồi trống hoặc không hợp lệ")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        logging.error(f"Đã đạt số lần thử tối đa ({self.max_retries}), sử dụng phản hồi mặc định")
                        fallback_response = "Xin lỗi, tôi đang gặp sự cố kỹ thuật. Bạn có thể để lại thông tin liên hệ để chúng tôi hỗ trợ bạn sau không?"
                        if message:
                            self.update_history("user", message)
                        self.update_history("assistant", fallback_response)
                        return fallback_response
                        
            except Exception as e:
                retry_count += 1
                if retry_count <= self.max_retries:
                    logging.warning(f"Left agent API error (lần thử {retry_count}): {e}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logging.error(f"Left agent error sau {self.max_retries} lần thử: {e}")
                    fallback_response = f"Xin lỗi, tôi đang gặp vấn đề kỹ thuật. Tôi sẽ liên hệ lại với bạn sau."
                    if message:
                        self.update_history("user", message)
                    self.update_history("assistant", fallback_response)
                    return fallback_response