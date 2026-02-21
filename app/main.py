"""FastAPI application for Question-Answering bot."""
import os
import tempfile
import time
import json
import logging
from typing import Dict, List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.document_loader import load_pdf, load_json, load_questions
from app.qa_service import QAService

# Setup structured logging
class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON structured logs."""
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name
        }
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        return json.dumps(log_data)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Constants for request validation
MAX_FILE_SIZE_MB = 50  # Maximum file size in MB
MAX_QUESTIONS = 100    # Maximum number of questions per request
MAX_QUESTION_LENGTH = 1000  # Maximum length of a single question

app = FastAPI(
    title="Zania QA Bot API",
    description="Question-Answering bot API using LangChain and OpenAI",
    version="1.0.0"
)

# Track startup time for metrics
@app.on_event("startup")
async def startup_event():
    app.state.start_time = time.time()
    logger.info("Application started", extra={'extra_data': {'version': '1.0.0'}})

# Global QA service instance
qa_service = QAService()

# Metrics storage (in production, use proper metrics system)
metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_questions_processed": 0,
    "average_response_time": 0.0,
    "total_tokens_used": 0  # Would need to track from OpenAI responses
}


class QuestionAnswerResponse(BaseModel):
    """Response model for question-answer pairs."""
    results: Dict[str, str]


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Zania QA Bot API",
        "version": "1.0.0",
        "endpoints": {
            "POST /qa": "Process questions and documents",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/metrics")
async def get_metrics():
    """Get API metrics."""
    return {
        "metrics": metrics,
        "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    }


@app.post("/qa", response_model=QuestionAnswerResponse)
async def process_qa(
    questions_file: UploadFile = File(..., description="JSON file containing questions"),
    document_file: UploadFile = File(..., description="PDF or JSON file containing the document")
):
    """
    Process questions and document to generate answers.
    
    Args:
        questions_file: JSON file containing a list of questions
        document_file: PDF or JSON file containing the document content
        
    Returns:
        JSON response with question-answer pairs
        
    Raises:
        HTTPException: For invalid file types, size limits, or question count
    """
    request_start_time = time.time()
    metrics["total_requests"] += 1
    
    try:
        # Validate questions file type
        if not questions_file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Questions file must be a JSON file"
            )
        
        # Validate document file type
        doc_ext = os.path.splitext(document_file.filename)[1].lower()
        if doc_ext not in ['.pdf', '.json']:
            raise HTTPException(
                status_code=400,
                detail="Document file must be a PDF or JSON file"
            )
        
        # Save uploaded files temporarily
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save and validate questions file
            questions_path = os.path.join(temp_dir, "questions.json")
            questions_content = await questions_file.read()
            
            # Check file size
            questions_size_mb = len(questions_content) / (1024 * 1024)
            if questions_size_mb > MAX_FILE_SIZE_MB:
                raise HTTPException(
                    status_code=413,
                    detail=f"Questions file size ({questions_size_mb:.2f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
                )
            
            with open(questions_path, "wb") as f:
                f.write(questions_content)
            
            # Save and validate document file
            doc_path = os.path.join(temp_dir, f"document{doc_ext}")
            document_content = await document_file.read()
            
            # Check file size
            doc_size_mb = len(document_content) / (1024 * 1024)
            if doc_size_mb > MAX_FILE_SIZE_MB:
                raise HTTPException(
                    status_code=413,
                    detail=f"Document file size ({doc_size_mb:.2f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
                )
            
            with open(doc_path, "wb") as f:
                f.write(document_content)
            
            # Load and validate questions
            questions = load_questions(questions_path)
            
            if not questions:
                raise HTTPException(
                    status_code=400,
                    detail="No questions found in the questions file"
                )
            
            # Check question count limit
            if len(questions) > MAX_QUESTIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Number of questions ({len(questions)}) exceeds maximum allowed ({MAX_QUESTIONS})"
                )
            
            # Validate individual question lengths
            for question in questions:
                if len(question) > MAX_QUESTION_LENGTH:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters"
                    )
            
            # Load document
            if doc_ext == '.pdf':
                document_text = load_pdf(doc_path)
            else:
                document_text = load_json(doc_path)
            
            if not document_text or not document_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Document file is empty or could not be processed"
                )
            
            # Process with QA service
            qa_service.load_document(document_text)
            results = qa_service.answer_questions(questions)
            
            # Calculate metrics
            request_time = time.time() - request_start_time
            metrics["successful_requests"] += 1
            metrics["total_questions_processed"] += len(questions)
            metrics["average_response_time"] = (
                (metrics["average_response_time"] * (metrics["successful_requests"] - 1) + request_time) 
                / metrics["successful_requests"]
            )
            
            # Log successful processing with metrics
            logger.info("QA processing completed successfully", extra={
                'extra_data': {
                    'num_questions': len(questions),
                    'document_type': doc_ext,
                    'document_size_bytes': len(document_text),
                    'response_time_seconds': round(request_time, 3),
                    'questions_per_second': round(len(questions) / request_time, 2) if request_time > 0 else 0
                }
            })
            
            return QuestionAnswerResponse(results=results)
            
    except ValueError as e:
        metrics["failed_requests"] += 1
        logger.error("Validation error", extra={'extra_data': {'error': str(e)}})
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        metrics["failed_requests"] += 1
        raise
    except Exception as e:
        metrics["failed_requests"] += 1
        logger.error("Processing error", extra={'extra_data': {'error': str(e)}})
        raise HTTPException(
            status_code=500,
            detail=f"Error processing files: {str(e)}"
        )


@app.post("/qa/batch")
async def process_qa_batch(
    questions: List[str],
    document_text: str
):
    """
    Process questions with document text directly (for testing).
    
    Args:
        questions: List of questions
        document_text: Document text content
        
    Returns:
        JSON response with question-answer pairs
    """
    try:
        qa_service.load_document(document_text)
        results = qa_service.answer_questions(questions)
        return QuestionAnswerResponse(results=results)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
