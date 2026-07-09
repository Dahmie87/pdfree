"""FastAPI app for PDF book generation agent."""

import os
import logging
import re
import time
from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.responses import FileResponse  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from pydantic import BaseModel, ConfigDict, Field, AliasChoices
from typing import Literal
from agent.book_agent import BookGenerationAgent
from models.llm import is_groq_daily_quota_error

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


def _is_rate_limit_error(error: Exception) -> bool:
    """Detect Groq daily quota exhaustion from the structured error payload."""
    return is_groq_daily_quota_error(error)


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

    Illegal characters: < > : " | ? * plus slash and backslash, and control characters
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
    model_config = ConfigDict(populate_by_name=True)

    prompt: str
    length_priority: Literal["length", "balanced",
                             "fast", "super_fast"] | None = "balanced"
    theme: Literal["casual", "professional",
                   "creative", "technical"] = Field(
        default="casual",
        description="Writing mode that controls tone, typography, and decorative style.",
        validation_alias=AliasChoices("theme", "writing_mode"),
    )
    # Optional custom filename (without .pdf extension)
    filename: str | None = None
    # Optional client-provided version string (e.g. "pdfree:1.3")
    version: str | None = None
    # Cover design choice: available options documented in /generation/cover_designs.py
    cover_design: Literal["split", "frame", "stack", "bleed", "arch"] | None = "split"


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


@app.post("/generate-book")
def generate_book(request: BookRequest):
    """
    Generate a PDF book from a prompt.

    Args:
        request: BookRequest with 'prompt' field, optional 'length_priority', and optional 'filename'

    Returns:
        PDF file with generation time in response header
    """
    logger.info(
        f"📥 Received request: {request.prompt[:50]}... (length: {request.length_priority}, mode: {request.theme})")

    if not request.prompt or len(request.prompt.strip()) < 5:
        logger.warning("❌ Prompt too short")
        raise HTTPException(
            status_code=400,
            detail="Prompt must be at least 5 characters long"
        )

    try:
        logger.info("🔄 Starting book generation...")
        # Generate PDF with optional length priority
        pdf_bytes, title, generation_time = agent.generate_pdf_book(
            request.prompt,
            length_priority=request.length_priority,
            writing_mode=request.theme,
            cover_design=request.cover_design,
        )

        # Save temporarily with sanitized filename
        # Use provided filename or generate from title
        if request.filename:
            # Sanitize provided filename and add .pdf extension
            safe_filename = sanitize_filename(request.filename)
            filename = f"{safe_filename}.pdf"
        else:
            # Generate filename from title
            safe_title = sanitize_filename(title)
            filename = f"book_{safe_title}.pdf"
        filepath = f"/tmp/{filename}" if os.path.exists("/tmp") else filename

        logger.info(f"💾 Saving PDF to: {filepath}")
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"✅ PDF saved successfully: {len(pdf_bytes)} bytes")

        # Report the runtime version used by this backend.
        used_version = "pdfree:1.3"

        # Create response with timing and version headers
        response = FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/pdf"
        )
        # Add custom header with generation time
        response.headers["X-Generation-Time"] = f"{generation_time:.2f}"
        response.headers["X-Generation-Time-Unit"] = "seconds"
        # Report the version used for this request (does not change runtime behavior)
        response.headers["X-PDFree-Version"] = used_version

        return response

    except Exception as e:
        logger.error(f"❌ Error generating book: {str(e)}", exc_info=True)
        if _is_rate_limit_error(e):
            raise HTTPException(
                status_code=429,
                detail="Groq quota exhausted. Please try again later."
            )
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
