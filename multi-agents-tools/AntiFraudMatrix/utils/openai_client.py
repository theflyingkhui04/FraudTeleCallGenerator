from openai import OpenAI
import config
from typing import List, Dict, Any

class OpenAIClient:
    """Custom OpenAI API client, supports custom URLs"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.base_url = base_url or config.OPENAI_BASE_URL
        
        # Creating an OpenAI Client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat_completion(self, 
                      messages: List[Dict[str, str]], 
                      model: str = config.DEFAULT_MODEL,
                      temperature: float = 0.7,
                      max_tokens: int = 500,
                      stream: bool = False) -> str:
        """Call the ChatCompletion API to get the reply"""
        try:
            if not stream:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # Streaming response processing
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                
                # Collecting streaming response content
                collected_content = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content_chunk = chunk.choices[0].delta.content
                        collected_content += content_chunk
                        # You can add real-time processing logic here
                        
                return collected_content
                
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            # Try using an alternate model
            try:
                response = self.client.chat.completions.create(
                    model=config.FALLBACK_MODEL,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e2:
                print(f"The alternate model call also fails: {e2}")
                # Instead of returning an error message, an exception is thrown
                raise Exception(f"API call failed, main model error:{e}，Alternate model error：{e2}")