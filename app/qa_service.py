"""Question-Answering service using LangChain."""
import json
import logging
import time
import asyncio
from typing import List, Dict, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
try:
    from langchain.schema import Document
    from langchain.callbacks.base import BaseCallbackHandler
except ImportError:
    from langchain_core.documents import Document
    try:
        from langchain_core.callbacks import BaseCallbackHandler
    except ImportError:
        from langchain.callbacks.base import BaseCallbackHandler

from app.config import OPENAI_API_KEY, OPENAI_MODEL

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


class TokenUsageCallback(BaseCallbackHandler):
    """Callback to track token usage from LLM calls."""
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        
    def on_llm_end(self, response, **kwargs):
        """Called when LLM finishes."""
        try:
            if hasattr(response, 'llm_output') and response.llm_output:
                usage = response.llm_output.get('token_usage', {})
                if usage:
                    self.total_tokens += usage.get('total_tokens', 0)
                    self.prompt_tokens += usage.get('prompt_tokens', 0)
                    self.completion_tokens += usage.get('completion_tokens', 0)
            elif hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                if usage:
                    self.total_tokens += usage.get('total_tokens', 0)
                    self.prompt_tokens += usage.get('prompt_tokens', 0)
                    self.completion_tokens += usage.get('completion_tokens', 0)
        except Exception as e:
            logger.debug(f"Error extracting token usage from callback: {e}")
    
    def reset(self):
        """Reset token counts."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0


class QAService:
    """Service for answering questions based on document content."""
    
    def __init__(self):
        """Initialize the QA service with embeddings and LLM."""
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            openai_api_key=OPENAI_API_KEY,
            temperature=0,
            timeout=30  # 30 second timeout for LLM calls
        )
        self.vectorstore = None
        self.qa_chain = None
        self.last_token_usage = 0  # Track token usage from last operation
        
    def load_document(self, document_text: str):
        """
        Load document text and create vector store.
        
        Args:
            document_text: The text content of the document
        """
        start_time = time.time()
        
        # Split text into chunks with optimal size
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        texts = text_splitter.split_text(document_text)
        documents = [Document(page_content=text) for text in texts]
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        
        # Create QA chain with custom prompt for better grounding
        prompt_template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer based on the provided context, respond with exactly: "Information not found in the provided documents."
        Don't try to make up an answer. Be concise and accurate in your response.
        Cite specific information from the context when possible.

        Context: {context}

        Question: {question}

        Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}  # Retrieve top 3 relevant chunks
            ),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True  # Enable source documents for citations
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Document loaded and indexed", extra={
            'extra_data': {
                'num_chunks': len(documents),
                'document_length': len(document_text),
                'indexing_time_seconds': round(elapsed, 3)
            }
        })
    
    async def answer_question_async(self, question: str) -> Dict[str, any]:
        """
        Answer a single question asynchronously.
        
        Args:
            question: The question to answer
            
        Returns:
            Dictionary with answer and metadata
        """
        if not self.qa_chain:
            raise ValueError("Document must be loaded before answering questions")
        
        start_time = time.time()
        # Create a new callback for this invocation to avoid race conditions
        token_callback = TokenUsageCallback()
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.qa_chain.invoke(
                    {"query": question},
                    config={"callbacks": [token_callback]}  # Pass callback to this invocation
                )
            )
            
            answer = response.get("result", "Unable to generate answer")
            source_docs = response.get("source_documents", [])
            
            # Get token usage from callback (most reliable method)
            token_usage = token_callback.total_tokens
            
            # Fallback: Try to extract from response if callback didn't capture it
            if token_usage == 0:
                try:
                    # Try to get from response dict directly
                    if isinstance(response, dict):
                        # Check for llm_output in response
                        if 'llm_output' in response and response['llm_output']:
                            usage = response['llm_output'].get('token_usage', {})
                            if usage:
                                token_usage = usage.get('total_tokens', 0)
                        # Check if response has usage_metadata (newer LangChain versions)
                        elif 'usage_metadata' in response:
                            usage = response['usage_metadata']
                            token_usage = usage.get('total_tokens', 0) if isinstance(usage, dict) else 0
                    # Try to get from response object attributes
                    elif hasattr(response, 'llm_output') and response.llm_output:
                        usage = getattr(response.llm_output, 'token_usage', {})
                        if isinstance(usage, dict):
                            token_usage = usage.get('total_tokens', 0)
                    elif hasattr(response, 'usage_metadata'):
                        usage = response.usage_metadata
                        if hasattr(usage, 'total_tokens'):
                            token_usage = usage.total_tokens
                        elif isinstance(usage, dict):
                            token_usage = usage.get('total_tokens', 0)
                except Exception as e:
                    logger.debug(f"Could not extract token usage: {e}")
                    token_usage = 0
            
            # Check if answer indicates not found
            is_not_found = (
                "Information not found" in answer or
                "not found in the provided documents" in answer.lower() or
                answer == "Unable to generate answer"
            )
            
            elapsed = time.time() - start_time
            
            return {
                "answer": answer,
                "found": not is_not_found,
                "source_count": len(source_docs),
                "response_time": round(elapsed, 3),
                "token_usage": token_usage
            }
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Error answering question", extra={
                'extra_data': {
                    'error': str(e),
                    'response_time_seconds': round(elapsed, 3)
                }
            })
            raise
    
    async def answer_questions(self, questions: List[str]) -> Dict[str, str]:
        """
        Answer a list of questions based on the loaded document.
        Uses async processing for better performance.
        
        Args:
            questions: List of questions to answer
            
        Returns:
            Dictionary mapping questions to answers
        """
        if not self.qa_chain:
            raise ValueError("Document must be loaded before answering questions")
        
        results = {}
        total_start_time = time.time()
        total_tokens = 0
        
        # Process questions concurrently (batch processing)
        try:
            tasks = [self.answer_question_async(q) for q in questions]
            answers = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in batch processing", extra={
                'extra_data': {'error': str(e)}
            })
            answers = [{"answer": f"Error: {str(e)}", "found": False, "token_usage": 0} for _ in questions]
        
        # Map results back to questions and accumulate token usage
        for question, answer_data in zip(questions, answers):
            if isinstance(answer_data, Exception):
                results[question] = f"Error processing question: {str(answer_data)}"
            else:
                results[question] = answer_data.get("answer", "Unable to generate answer")
                # Accumulate token usage
                total_tokens += answer_data.get("token_usage", 0)
        
        total_time = time.time() - total_start_time
        
        # Store total tokens for metrics access
        self.last_token_usage = total_tokens
        
        # Log metrics
        successful = len([r for r in results.values() if not r.startswith('Error')])
        logger.info(f"Batch processing completed", extra={
            'extra_data': {
                'total_questions': len(questions),
                'successful_answers': successful,
                'total_time_seconds': round(total_time, 3),
                'average_time_per_question': round(total_time / len(questions), 3) if questions else 0,
                'throughput_questions_per_second': round(len(questions) / total_time, 2) if total_time > 0 else 0,
                'total_tokens_used': total_tokens
            }
        })
        
        return results
    
    def cleanup(self):
        """Clean up resources."""
        if self.vectorstore:
            # ChromaDB will persist automatically, but we can clear if needed
            pass
