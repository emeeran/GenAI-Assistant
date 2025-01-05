from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str

@dataclass
class Choice:
    message: Message
    finish_reason: Optional[str] = None

@dataclass
class Response:
    choices: List[Choice]
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None

class ResponseHandler:
    @staticmethod
    def format_response(data: Any) -> Response:
        """Format various response types into a standardized Response object"""
        try:
            if isinstance(data, Response):
                return data

            if isinstance(data, dict):
                # Handle dictionary response
                if "choices" in data:
                    choices = [
                        Choice(
                            message=Message(
                                role=choice.get("message", {}).get("role", "assistant"),
                                content=choice.get("message", {}).get("content", "")
                            ),
                            finish_reason=choice.get("finish_reason")
                        )
                        for choice in data["choices"]
                    ]
                else:
                    # Handle simple content response
                    choices = [
                        Choice(
                            message=Message(
                                role="assistant",
                                content=data.get("content", str(data))
                            )
                        )
                    ]

                return Response(
                    choices=choices,
                    model=data.get("model"),
                    usage=data.get("usage")
                )

            # Handle string or other simple responses
            return Response(choices=[
                Choice(message=Message(role="assistant", content=str(data)))
            ])

        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return Response(choices=[
                Choice(message=Message(
                    role="assistant",
                    content=f"Error: Failed to process response - {str(e)}"
                ))
            ])

    @staticmethod
    def validate_response(response: Response) -> bool:
        """Validate response structure and content"""
        try:
            if not response.choices:
                return False

            for choice in response.choices:
                if not choice.message or not choice.message.content:
                    return False

                # Check for error messages
                if choice.message.content.startswith("Error:"):
                    return False

            return True

        except Exception:
            return False

    @staticmethod
    def extract_content(response: Response) -> str:
        """Extract content from response safely"""
        try:
            if not response.choices:
                raise ValueError("No choices in response")

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty content in response")

            return content

        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return f"Error: Failed to extract response content - {str(e)}"
