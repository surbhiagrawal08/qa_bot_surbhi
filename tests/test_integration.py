"""Integration tests for QA API with mocked LLM."""
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls and LangChain components."""
    with patch('app.qa_service.OpenAIEmbeddings') as mock_embeddings, \
         patch('app.qa_service.ChatOpenAI') as mock_llm, \
         patch('app.qa_service.Chroma') as mock_chroma, \
         patch('app.qa_service.RetrievalQA') as mock_retrieval_qa:
        
        # Mock embeddings
        mock_emb_instance = Mock()
        mock_embeddings.return_value = mock_emb_instance
        
        # Mock LLM
        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance
        
        # Mock vector store
        mock_vectorstore = Mock()
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents = Mock(return_value=[
            Mock(page_content="Mocked document chunk 1"),
            Mock(page_content="Mocked document chunk 2")
        ])
        mock_vectorstore.as_retriever = Mock(return_value=mock_retriever)
        mock_chroma.from_documents = Mock(return_value=mock_vectorstore)
        
        # Mock QA chain - this is what actually gets called
        mock_qa_chain_instance = Mock()
        mock_qa_chain_instance.invoke = Mock(return_value={
            "result": "Mocked answer from document",
            "source_documents": [
                Mock(page_content="Mocked document chunk 1"),
                Mock(page_content="Mocked document chunk 2")
            ]
        })
        mock_retrieval_qa.from_chain_type = Mock(return_value=mock_qa_chain_instance)
        
        yield {
            'embeddings': mock_emb_instance,
            'llm': mock_llm_instance,
            'vectorstore': mock_vectorstore,
            'qa_chain': mock_qa_chain_instance
        }


@pytest.fixture
def sample_questions_file():
    """Create a temporary questions file."""
    questions = [
        "What is the main topic?",
        "Who is the author?"
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(questions, f)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def sample_document_file():
    """Create a temporary document file."""
    content = b"Sample PDF content for testing"
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


def test_qa_endpoint_with_mocked_llm(mock_openai, sample_questions_file):
    """Test QA endpoint with mocked LLM dependencies - tests actual LLM integration."""
    # Configure the mock QA chain to return different answers for different questions
    def mock_invoke(query_dict):
        question = query_dict.get("query", "")
        if "main topic" in question.lower():
            return {
                "result": "Test topic",
                "source_documents": [Mock(page_content="Document about testing")]
            }
        elif "author" in question.lower():
            return {
                "result": "Test author",
                "source_documents": [Mock(page_content="Document about author")]
            }
        return {
            "result": "Mocked answer",
            "source_documents": []
        }
    
    mock_openai['qa_chain'].invoke = Mock(side_effect=mock_invoke)
    
    # Use JSON document instead of PDF to avoid parsing issues
    doc_data = {"content": "This is a test document with information about testing."}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(doc_data, f)
        doc_path = f.name
    
    try:
        with open(sample_questions_file, 'rb') as qf, open(doc_path, 'rb') as df:
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
        assert isinstance(data["results"], dict)
        # Verify that the mocked LLM was actually called (integration test)
        assert mock_openai['qa_chain'].invoke.called
    finally:
        os.unlink(doc_path)


def test_qa_endpoint_json_document(mock_openai, sample_questions_file):
    """Test QA endpoint with JSON document - tests LLM integration with JSON docs."""
    # Configure mock to return test answers
    mock_openai['qa_chain'].invoke = Mock(return_value={
        "result": "Test topic",
        "source_documents": [Mock(page_content="Test document content")]
    })
    
    # Create JSON document
    doc_data = {"content": "This is a test document with information about testing."}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(doc_data, f)
        doc_path = f.name
    
    try:
        with open(sample_questions_file, 'rb') as qf, open(doc_path, 'rb') as df:
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
        # Verify LLM chain was called (integration test)
        assert mock_openai['qa_chain'].invoke.called
    finally:
        os.unlink(doc_path)


def test_qa_endpoint_multiple_questions(mock_openai, sample_questions_file):
    """Test QA endpoint with multiple questions - tests LLM integration with batch processing."""
    # Create questions file with multiple questions
    questions = [
        "Question 1?",
        "Question 2?",
        "Question 3?",
        "Question 4?",
        "Question 5?"
    ]
    
    # Configure mock to return different answers for each question
    call_count = [0]  # Use list to allow modification in closure
    def mock_invoke(query_dict):
        question = query_dict.get("query", "")
        call_count[0] += 1
        return {
            "result": f"Answer to {question}",
            "source_documents": [Mock(page_content=f"Content for {question}")]
        }
    
    mock_openai['qa_chain'].invoke = Mock(side_effect=mock_invoke)
    
    # Use JSON document instead of PDF to avoid parsing issues
    doc_data = {"content": "This is a test document with multiple pieces of information for testing."}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(doc_data, f)
        doc_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(questions, f)
        questions_path = f.name
    
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
        assert len(data["results"]) == 5
        for q in questions:
            assert q in data["results"]
        # Verify LLM was called for each question (integration test)
        assert mock_openai['qa_chain'].invoke.call_count == 5
    finally:
        os.unlink(questions_path)
        os.unlink(doc_path)


def test_qa_endpoint_file_size_limit(mock_openai):
    """Test QA endpoint with file size limit."""
    # Create large questions file (simulate)
    large_content = b"x" * (51 * 1024 * 1024)  # 51 MB
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        f.write(large_content)
        large_file = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"small pdf")
        small_pdf = f.name
    
    try:
        with open(large_file, 'rb') as qf, open(small_pdf, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.json", qf, "application/json"),
                    "document_file": ("document.pdf", df, "application/pdf")
                }
            )
        
        assert response.status_code == 413  # Payload Too Large
    finally:
        os.unlink(large_file)
        os.unlink(small_pdf)


def test_qa_endpoint_invalid_file_types():
    """Test QA endpoint with invalid file types."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not json")
        txt_file = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(b"pdf content")
        pdf_file = f.name
    
    try:
        with open(txt_file, 'rb') as qf, open(pdf_file, 'rb') as df:
            response = client.post(
                "/qa",
                files={
                    "questions_file": ("questions.txt", qf, "text/plain"),
                    "document_file": ("document.pdf", df, "application/pdf")
                }
            )
        
        assert response.status_code == 400
        assert "must be a JSON file" in response.json()["detail"]
    finally:
        os.unlink(txt_file)
        os.unlink(pdf_file)
