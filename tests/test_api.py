"""Tests for FastAPI endpoints."""
import json
import os
import tempfile
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_qa_endpoint_invalid_questions_file():
    """Test QA endpoint with invalid questions file type."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not json")
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"fake pdf content")
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.txt", qf, "text/plain"),
                    "document_file": ("document.pdf", df, "application/pdf")
                }
            )
            assert response.status_code == 400
            assert "JSON" in response.json()["detail"]
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


def test_qa_endpoint_invalid_document_file():
    """Test QA endpoint with invalid document file type."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(["Question 1?"], f)
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not pdf or json")
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.json", qf, "application/json"),
                    "document_file": ("document.txt", df, "text/plain")
                }
            )
            assert response.status_code == 400
            assert "PDF or JSON" in response.json()["detail"]
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


def test_qa_endpoint_empty_questions():
    """Test QA endpoint with empty questions array."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"content": "Sample document content"}, f)
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.json", qf, "application/json"),
                    "document_file": ("document.json", df, "application/json")
                }
            )
            assert response.status_code == 400
            assert "No questions" in response.json()["detail"]
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


def test_qa_endpoint_exceeds_question_limit():
    """Test QA endpoint with too many questions."""
    # Create questions that exceed MAX_QUESTIONS (100)
    questions = [f"Question {i}?" for i in range(105)]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(questions, f)
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"content": "Sample document"}, f)
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.json", qf, "application/json"),
                    "document_file": ("document.json", df, "application/json")
                }
            )
            assert response.status_code == 400
            assert "exceeds maximum" in response.json()["detail"]
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


def test_qa_endpoint_empty_document():
    """Test QA endpoint with empty document."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(["What is this?"], f)
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"content": ""}, f)
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.json", qf, "application/json"),
                    "document_file": ("document.json", df, "application/json")
                }
            )
            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


@patch('app.qa_service.QAService.answer_questions', new_callable=AsyncMock)
def test_qa_endpoint_success_with_mocked_llm(mock_answer):
    """Test successful QA endpoint with mocked LLM."""
    # Mock the answer_questions method (now async)
    mock_answer.return_value = {
        "What is AI?": "AI is Artificial Intelligence.",
        "What is ML?": "ML is Machine Learning."
    }
    
    questions = ["What is AI?", "What is ML?"]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(questions, f)
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"content": "AI and ML are subsets of computer science"}, f)
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.json", qf, "application/json"),
                    "document_file": ("document.json", df, "application/json")
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2
            assert "What is AI?" in data["results"]
            assert data["results"]["What is AI?"] == "AI is Artificial Intelligence."
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


def test_batch_endpoint_basic():
    """Test batch endpoint with direct text input."""
    payload = {
        "questions": ["What is AI?", "What is ML?"],
        "document_text": "AI stands for Artificial Intelligence. ML stands for Machine Learning."
    }
    
    with patch('app.qa_service.QAService.answer_questions', new_callable=AsyncMock) as mock_answer:
        mock_answer.return_value = {
            "What is AI?": "AI stands for Artificial Intelligence.",
            "What is ML?": "ML stands for Machine Learning."
        }
        
        response = client.post("/qa/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2


def test_response_format_validity():
    """Test that response format is valid JSON with expected structure."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(["Test question?"], f)
        questions_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"content": "Test document content"}, f)
        doc_path = f.name
    
    try:
        with open(questions_path, 'rb') as qf, open(doc_path, 'rb') as df:
            with patch('app.qa_service.QAService.answer_questions', new_callable=AsyncMock) as mock_answer:
                mock_answer.return_value = {"Test question?": "Test answer"}
                
                response = client.post(
                    "/qa",
                    files={
                        "questions_file": ("questions.json", qf, "application/json"),
                        "document_file": ("document.json", df, "application/json")
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert isinstance(data, dict)
                assert "results" in data
                assert isinstance(data["results"], dict)
                assert all(
                    isinstance(k, str) and isinstance(v, str)
                    for k, v in data["results"].items()
                )
    finally:
        # Clean up temporary files
        if os.path.exists(questions_path):
            os.unlink(questions_path)
        if os.path.exists(doc_path):
            os.unlink(doc_path)