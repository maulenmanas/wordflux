import google.generativeai as genai
import logging
import asyncio

logger = logging.getLogger(__name__)

class GeminiClientManager:
    """Quản lý Gemini API client"""

    def __init__(self, api_key: str):
        """
        Khởi tạo Gemini client
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("Gemini API key not found. Please check your config.yaml file.")
        
        genai.configure(api_key=self.api_key)
        self.client = genai

    def get_client(self):
        """Trả về Gemini client module (since it's module level configuration mostly)"""
        return self.client
