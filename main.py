"""FastAPI app for PDF book generation agent."""

import os
import logging
import re
from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.responses import FileResponse  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel
from agent.book_agent import BookGenerationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()
logger.info("✅ Environment variables loaded")

app = FastAPI(
    title="PDFree - Book Generation Agent",
    description="Generate PDF books from prompts using LangChain",
    version="0.1.0"
)

# Add CORS middleware (must be BEFORE routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],                    # Allow all origins
    # Must be False when allow_origins=["*"]
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

logger.info("✅ CORS middleware configured - allowing all origins")

# Initialize agent
logger.info("🚀 Initializing BookGenerationAgent...")
try:
    agent = BookGenerationAgent()
    logger.info("✅ Agent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize agent: {e}")
    raise


def sanitize_filename(filename: str) -> str:
    """
    Remove illegal characters from filename for Windows/Unix compatibility.

    Illegal characters: < > : " | ? * / \ and control characters
    """
    # Remove illegal characters
    illegal_chars = r'[<>:"|?*\\/]'
    sanitized = re.sub(illegal_chars, '', filename)
    # Replace multiple spaces with single underscore
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Limit length
    sanitized = sanitized[:50]
    return sanitized


class BookRequest(BaseModel):
    """Request model for book generation."""
    prompt: str
    pages: int = 20  # Default 20 pages (~5 chapters)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "PDFree Book Generation Agent",
        "endpoint": "/generate-book (POST)",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():  # type: ignore
    """Health check endpoint."""
    logger.info("💚 Health check")
    return {"status": "ok", "message": "PDFree backend is running"}


@app.options("/health")
def options_health():
    """Handle CORS preflight for health."""
    return {"message": "OK"}


@app.options("/generate-book")
def options_generate_book():
    """Handle CORS preflight requests."""
    return {"message": "OK"}


@app.post("/generate-book")
def generate_book(request: BookRequest):
    """
    Generate a PDF book from a prompt.

    Args:
        request: BookRequest with 'prompt' field and optional 'pages' (default 20)

    Returns:
        PDF file
    """
    logger.info(
        f"📥 Received request: {request.prompt[:50]}... (pages: {request.pages})")

    if not request.prompt or len(request.prompt.strip()) < 5:
        logger.warning("❌ Prompt too short")
        raise HTTPException(
            status_code=400,
            detail="Prompt must be at least 5 characters long"
        )

    # Validate pages parameter
    if request.pages < 10 or request.pages > 500:
        logger.warning(f"❌ Pages out of range: {request.pages}")
        raise HTTPException(
            status_code=400,
            detail="Pages must be between 10 and 500"
        )

    try:
        logger.info("🔄 Starting book generation...")
        # Generate PDF with specified number of pages
        pdf_bytes, title = agent.generate_pdf_book(
            request.prompt, desired_pages=request.pages)

        # Save temporarily with sanitized filename
        safe_title = sanitize_filename(title)
        filename = f"book_{safe_title}.pdf"
        filepath = f"/tmp/{filename}" if os.path.exists("/tmp") else filename

        logger.info(f"💾 Saving PDF to: {filepath}")
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"✅ PDF saved successfully: {len(pdf_bytes)} bytes")
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/pdf"
        )

    except Exception as e:
        logger.error(f"❌ Error generating book: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating book: {str(e)}"
        )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    logger.info("💚 Health check")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn  # type: ignore
    logger.info("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
