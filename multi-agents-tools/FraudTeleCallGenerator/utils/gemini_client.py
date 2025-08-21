"""
Gemini API Client - Tối ưu hóa rate limiting và exponential backoff
"""

import requests
import json
import time
import random
import logging
from typing import Dict, List, Any, Optional
from threading import Lock

class GeminiClient:
    """Client để gọi API Gemini của Google"""
    
    # Class-level lock để đồng bộ hóa requests giữa các instances
    _request_lock = Lock()
    _last_request_time = 0
    _min_request_interval = 0.5  # Tối thiểu 0.5 giây giữa các requests
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        
    def _wait_for_rate_limit(self):
        """Đảm bảo tuân thủ rate limit bằng cách chờ giữa các requests"""
        with self._request_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < self._min_request_interval:
                wait_time = self._min_request_interval - time_since_last
                # Thêm jitter để tránh thundering herd
                jitter = random.uniform(0, 0.2)
                wait_time += jitter
                time.sleep(wait_time)
            
            self._last_request_time = time.time()
        
    def _make_request(self, messages: List[Dict], max_retries: int = 5) -> Optional[str]:
        """Gửi request tới Gemini API"""
        
        # Áp dụng rate limiting trước khi gửi request
        self._wait_for_rate_limit()
        self.request_count += 1
        
        # Convert OpenAI format messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if not content.strip():  # Skip empty content
                continue
                
            if role == "system":
                system_instruction = content
            elif role in ["user", "assistant"]:
                # Gemini chỉ có "user" và "model", không có "assistant"
                gemini_role = "user" if role == "user" else "model"
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
        
        # Nếu không có contents nào (chỉ có system), tạo một dummy user message
        if not contents and system_instruction:
            contents.append({
                "role": "user", 
                "parts": [{"text": "Hãy bắt đầu cuộc hội thoại."}]
            })
        
        # Nếu vẫn không có contents, báo lỗi
        if not contents:
            self.logger.error("❌ Không có nội dung hợp lệ để gửi tới Gemini")
            return None
        
        # Prepare request data
        request_data: Dict[str, Any] = {
            "contents": contents
        }
        
        # Add system instruction if exists
        if system_instruction:
            request_data["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        # Request configuration
        request_data["generationConfig"] = {
            "temperature": 0.8,
            "maxOutputTokens": 2048,
            "topP": 0.9,
            "topK": 40
        }
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Gửi request tới Gemini API (lần thử {attempt + 1}/{max_retries})")
                
                response = requests.post(
                    f"{url}?key={self.api_key}",
                    headers=headers,
                    json=request_data,
                    timeout=90  # Tăng timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                      # Parse response
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            text = candidate["content"]["parts"][0].get("text", "")
                            # Normalize newlines để đảm bảo JSONL format đúng
                            text = text.replace('\n', ' ').replace('\r', ' ').strip()
                            self.logger.info("✅ Gemini API response thành công")
                            return text
                    
                    self.logger.warning(f"⚠️ Gemini response không có content: {result}")
                    return None
                    
                elif response.status_code == 429:
                    # Improved exponential backoff cho rate limit
                    base_wait = min(2 ** attempt, 60)  # Max 60 giây
                    jitter = random.uniform(0.5, 1.5)
                    wait_time = base_wait * jitter
                    
                    self.logger.warning(f"🚫 Rate limit (429), đợi {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                    # Tăng interval tối thiểu sau rate limit
                    self._min_request_interval = min(self._min_request_interval * 1.5, 2.0)
                    continue
                    
                elif response.status_code in [500, 502, 503, 504]:
                    # Server errors - retry với backoff
                    wait_time = min(2 ** attempt, 30) + random.uniform(0, 5)
                    self.logger.warning(f"🔄 Server error {response.status_code}, retry sau {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    self.logger.error(f"❌ Gemini API error {response.status_code}: {response.text}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(2 ** attempt)
                    
            except requests.exceptions.Timeout:
                wait_time = min(5 * (attempt + 1), 30)
                self.logger.warning(f"⏰ Timeout lần thử {attempt + 1}, đợi {wait_time}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                continue
                
            except requests.exceptions.ConnectionError:
                wait_time = min(5 * (attempt + 1), 30)
                self.logger.warning(f"🔌 Connection error lần thử {attempt + 1}, đợi {wait_time}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                continue
                
            except Exception as e:
                wait_time = min(3 * (attempt + 1), 20)
                self.logger.error(f"❌ Exception khi gọi Gemini API: {e}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                continue
        
        self.logger.error(f"❌ Gemini API failed sau {max_retries} lần thử")
        return None
    
    def chat_completion(self, messages: List[Dict], **kwargs) -> Optional[str]:
        """Interface tương thích với OpenAI client"""
        return self._make_request(messages)

def create_gemini_client(api_key: str, model: str = "gemini-2.0-flash") -> GeminiClient:
    """Factory function để tạo Gemini client"""
    return GeminiClient(api_key=api_key, model=model)
