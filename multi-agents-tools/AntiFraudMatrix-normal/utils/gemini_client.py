#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API Client - Thay thế OpenAI client cho Google Gemini
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional

class GeminiClient:
    """Client để gọi API Gemini của Google"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, messages: List[Dict], max_retries: int = 3) -> Optional[str]:
        """Gửi request tới Gemini API"""
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
        request_data = {
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
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Parse response
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            text = candidate["content"]["parts"][0].get("text", "")
                            self.logger.info("✅ Gemini API response thành công")
                            return text
                    
                    self.logger.warning(f"⚠️ Gemini response không có content: {result}")
                    return None
                    
                elif response.status_code == 429:
                    # Rate limit
                    wait_time = 2 ** attempt
                    self.logger.warning(f"🚫 Rate limit (429), đợi {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    self.logger.error(f"❌ Gemini API error {response.status_code}: {response.text}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(1)
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"⏰ Timeout lần thử {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue
                
            except Exception as e:
                self.logger.error(f"❌ Exception khi gọi Gemini API: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue
        
        return None
    
    def chat_completion(self, messages: List[Dict], **kwargs) -> Optional[str]:
        """Interface tương thích với OpenAI client"""
        return self._make_request(messages)

def create_gemini_client(api_key: str, model: str = "gemini-2.0-flash") -> GeminiClient:
    """Factory function để tạo Gemini client"""
    return GeminiClient(api_key=api_key, model=model)
