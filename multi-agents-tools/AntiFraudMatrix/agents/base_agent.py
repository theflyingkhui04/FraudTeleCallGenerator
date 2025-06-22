from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from utils.openai_client import OpenAIClient
from utils.gemini_client import GeminiClient

class BaseAgent(ABC):
    """Lớp trừu tượng cơ bản cho các agent, định nghĩa giao diện chung cho tất cả agent"""
    
    def __init__(self, role: str, model: Optional[str] = None, base_url: Optional[str] = None, 
                 api_key: Optional[str] = None, use_gemini: bool = False):
        self.role = role
        self.model = model
        self.conversation_history = []
        self.use_gemini = use_gemini
        
        if use_gemini and api_key:
            # Sử dụng Gemini client
            self.client = GeminiClient(api_key=api_key, model=model or "gemini-2.0-flash")
        else:
            # Sử dụng OpenAI client (fallback)
            self.client = OpenAIClient(base_url=base_url or "")
        
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Trả về prompt hệ thống"""
        pass
    
    @abstractmethod
    def generate_response(self, message: str) -> str:
        """Sinh phản hồi cho tin nhắn hiện tại"""
        pass
    
    def update_history(self, role: str, content: str) -> None:
        """Cập nhật lịch sử hội thoại"""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_history(self) -> List[Dict[str, str]]:
        """Lấy lịch sử hội thoại hiện tại"""
        return self.conversation_history
    
    def clear_history(self) -> None:
        """Xóa toàn bộ lịch sử hội thoại"""
        self.conversation_history = []

    def set_history(self, history: List[Dict[str, str]]) -> None:
        """Thiết lập lại lịch sử hội thoại"""
        self.conversation_history = history
