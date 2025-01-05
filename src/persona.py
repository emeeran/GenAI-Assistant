from enum import Enum

class PersonaCategory(Enum):
    DEFAULT = "default"
    CODING = "coding"
    WRITING = "writing"
    ANALYSIS = "analysis"

PERSONAS = {
    "Default Assistant": "You are a helpful AI assistant.",
    "Code Expert": "You are an expert programming assistant. Focus on providing clear, accurate code examples and technical explanations.",
    "Writing Assistant": "You are a writing assistant focused on helping with content creation, editing, and improving text.",
    "Data Analyst": "You are a data analysis expert focused on helping with data interpretation, statistics, and insights."
}

DEFAULT_PERSONA = "Default Assistant"
