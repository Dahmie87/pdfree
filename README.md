# PDFree - LangChain Book Generation Agent

Generate complete PDF books from simple prompts using LangChain and free resources.

## Features

- 🤖 LangChain-powered AI agent for book generation
- 📚 Generates structured, well-formatted PDF books
- 🔧 Free LLM via HuggingFace Inference API
- 🚀 FastAPI REST API for easy integration
- 💻 CLI tool for quick testing
- 📄 Professional PDF formatting with ReportLab

## Stack

- **LangChain**: Agent orchestration & LLM integration
- **HuggingFace**: Free LLM Inference API
- **ReportLab**: PDF generation
- **FastAPI**: REST API
- **Python 3.10+**: Runtime

## Quick Start

### Prerequisites

1. Install Python 3.10+
2. Install uv: `pip install uv` or `curl https://astral.sh/uv/install.sh | sh`
3. Create a free HuggingFace account at https://huggingface.co
4. Generate an API key at https://huggingface.co/settings/tokens
5. Accept model license (click to accept on model page)

### Setup

```bash
# Navigate to project
cd pdf_backend

# Create .env file with your HuggingFace API key
cp .env.example .env
# Edit .env and add your HUGGINGFACE_API_KEY

# Install dependencies with uv
uv sync
```

### Run API Server

```bash
# Using uv
uv run python main.py
```

Or directly:

```bash
python main.py
```

Server runs at `http://localhost:8000`

- API docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

### Generate a Book via API

```bash
curl -X POST "http://localhost:8000/generate-book" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a comprehensive guide to machine learning basics"}' \
  --output mybook.pdf
```

Or use Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/generate-book",
    json={"prompt": "Write about the history of artificial intelligence"}
)

with open("book.pdf", "wb") as f:
    f.write(response.content)
```

### CLI Usage

```bash
# Generate book from command line with uv
uv run python cli.py "Write a beginner's guide to Python programming"

# Or directly
python cli.py "Write a beginner's guide to Python programming"
```

## Configuration

Create `.env` file (copy from `.env.example`):

```env
# HuggingFace Configuration
# Get free API key from: https://huggingface.co/settings/tokens
HUGGINGFACE_API_KEY=your_api_key_here

# Model ID (optional, defaults to Mistral-7B)
# Other options: meta-llama/Llama-2-7b-chat-hf, tiiuae/falcon-7b-instruct
MODEL_ID=mistralai/Mistral-7B-Instruct-v0.1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Project Structure

```
pdf_backend/
├── main.py                 # FastAPI entry point
├── cli.py                  # CLI for testing
├── agent/
│   ├── book_agent.py      # Main orchestrator
│   └── prompts.py         # Prompt templates
├── generation/
│   └── pdf_generator.py   # PDF builder
├── models/
│   └── llm.py            # LLM initialization
├── pyproject.toml        # Dependencies
└── README.md             # This file
```

## API Endpoints

### `POST /generate-book`

Generate a PDF book from a prompt.

**Request:**

```json
{
  "prompt": "Write a book about climate change"
}
```

**Response:** PDF file (binary)

**Status Codes:**

- 200: Success
- 400: Invalid prompt (too short)
- 500: Generation error

### `GET /health`

Health check endpoint.

**Response:**

```json
{ "status": "ok" }
```

### `GET /`

Root endpoint with info.

## Troubleshooting

### "HUGGINGFACE_API_KEY not set" error

- Get a free API key from https://huggingface.co/settings/tokens
- Add it to `.env`: `HUGGINGFACE_API_KEY=your_key_here`

### "Model not found" or permission errors

- Accept model license: Visit https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1
- Click "Access repository" and accept terms
- Ensure your API token has read access

### "Connection timeout" error

- Check internet connection (HuggingFace API requires network access)
- Verify HuggingFace API is accessible from your region
- Try changing the MODEL_ID to a different model

### PDF generation fails

- Check available disk space
- Ensure all dependencies are installed: `uv sync`
- Check API response in terminal output for errors

## Performance Notes

- First generation takes longer (LLM reasoning + PDF creation)
- PDF size typically 20-100 KB depending on content
- Generation time: 30-120 seconds (depending on model and hardware)

## Future Enhancements

- Multiple output formats (EPUB, Markdown)
- Custom PDF styling options
- Batch generation
- Streaming responses for large books
- Model switching API endpoint

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
