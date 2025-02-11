from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class ResponseHandler:
    @staticmethod
    def extract_content(response: Any) -> str:
        """Extract content from various response types"""
        try:
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content
            elif isinstance(response, dict):
                return response.get('content', str(response))
            return str(response)
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return f"Error processing response: {str(e)}"
