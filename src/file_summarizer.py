from typing import Optional, Dict
from pathlib import Path


class FileSummarizer:
    def __init__(self):
        self.summary_prompts = {
            ".pdf": "Please summarize this PDF document: ",
            ".epub": "Please summarize this ebook: ",
            ".txt": "Please summarize this text: ",
            ".py": "Please explain this Python code: ",
            ".js": "Please explain this JavaScript code: ",
            ".json": "Please explain this JSON structure: ",
            ".md": "Please summarize this markdown document: ",
        }

    def get_summary_prompt(self, content: str, file_type: str, file_name: str) -> str:
        """Generate appropriate summary prompt based on file type"""
        base_prompt = self.summary_prompts.get(
            Path(file_name).suffix.lower(), "Please summarize this content: "
        )
        return f"{base_prompt}\n\nFile: {file_name}\n\n```\n{content}\n```"

    def get_context_prompt(self, content: str, file_name: str) -> str:
        """Generate a prompt for maintaining context about the file"""
        return (
            f"I have loaded a file named '{file_name}'. "
            f"You can refer to its content in our conversation. "
            f"What would you like to know about it?"
        )
