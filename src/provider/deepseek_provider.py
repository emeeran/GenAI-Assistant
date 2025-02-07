import os
from .base import BaseProvider
from openai import OpenAI
from typing import Dict, List, Any, Optional


class DeepSeekProvider(BaseProvider):
    """DeepSeek API provider implementation"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    def create_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-r1-dist-70b",
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a chat completion using DeepSeek API"""
        try:
            # Map simplified model names to full paths
            model_map = {
                "deepseek-r1-dist-70b": "deepseek-r1/deepseek-r1-dist-70b",
                "deepseek-chat-67b": "deepseek-ai/deepseek-llm-67b-chat",
                "deepseek-coder-33b": "deepseek-ai/deepseek-coder-33b",
            }

            full_model_name = model_map.get(model, model)
            response = self.client.chat.completions.create(
                model=full_model_name,
                messages=messages,
                temperature=temperature,
                **kwargs,
            )
            return {"content": response.choices[0].message.content, "role": "assistant"}
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")

    def get_models(self) -> List[str]:
        """Get available models"""
        return [
            "deepseek-ai/deepseek-llm-67b-chat",
            "deepseek-ai/deepseek-coder-33b",
            "deepseek-r1/deepseek-r1-dist-70b",
        ]
