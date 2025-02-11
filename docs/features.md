# GenAI Assistant Features

## Core Features

### Chat Interface
- Real-time chat interaction with AI
- Markdown support for messages
- Chat history display
- Message threading support

### File Processing
- Multi-format support: txt, py, js, json, csv, md, pdf, epub, images
- Automatic content extraction
- PDF text extraction
- EPUB text extraction
- OCR for images
- File summary generation

[...rest of existing feature documentation...]

## Development

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
streamlit run app.py
```

### Configuration
Set up your environment variables in `.env`:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
# ... other provider keys
```
