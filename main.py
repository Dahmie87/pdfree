"""FastAPI app for PDF book generation agent."""

import os
import logging
from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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

# Initialize agent
logger.info("🚀 Initializing BookGenerationAgent...")
try:
    agent = BookGenerationAgent()
    logger.info("✅ Agent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize agent: {e}")
    raise


class BookRequest(BaseModel):
    """Request model for book generation."""
    prompt: str


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "PDFree Book Generation Agent",
        "endpoint": "/generate-book (POST)",
        "docs": "/docs"
    }


@app.post("/generate-book")
def generate_book(request: BookRequest):
    """
    Generate a PDF book from a prompt.

    Args:
        request: BookRequest with 'prompt' field

    Returns:
        PDF file
    """
    logger.info(f"📥 Received request: {request.prompt[:50]}...")

    if not request.prompt or len(request.prompt.strip()) < 5:
        logger.warning("❌ Prompt too short")
        raise HTTPException(
            status_code=400,
            detail="Prompt must be at least 5 characters long"
        )

    try:
        logger.info("🔄 Starting book generation...")
        # Generate PDF
        pdf_bytes, title = agent.generate_pdf_book(request.prompt)

        # Save temporarily
        filename = f"book_{title.replace(' ', '_')[:20]}.pdf"
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
    import uvicorn
    logger.info("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
