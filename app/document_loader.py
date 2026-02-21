"""Document loaders for PDF and JSON files."""
import json
from typing import List
from pathlib import Path
from pypdf import PdfReader


def load_pdf(file_path: str) -> str:
    """
    Load and extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content as a string
    """
    reader = PdfReader(file_path)
    text_content = []
    
    for page in reader.pages:
        text_content.append(page.extract_text())
    
    return "\n\n".join(text_content)


def load_json(file_path: str) -> str:
    """
    Load and convert JSON file content to text.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        JSON content formatted as text
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle empty content - if dict has 'content' key with empty value, return empty string
    if isinstance(data, dict):
        # Check if it's a document with 'content' key
        if 'content' in data:
            content = data['content']
            if isinstance(content, str) and not content.strip():
                return ""  # Return empty string for empty content
            elif not content:  # None, empty list, etc.
                return ""
        
        # Convert JSON to a readable text format
        text_parts = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                text_parts.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                text_parts.append(f"{key}: {value}")
        return "\n".join(text_parts)
    elif isinstance(data, list):
        return "\n".join([json.dumps(item, indent=2) for item in data])
    else:
        return str(data)


def load_questions(file_path: str) -> List[str]:
    """
    Load questions from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing questions
        
    Returns:
        List of questions
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        # If it's a list of strings
        if all(isinstance(item, str) for item in data):
            return data
        # If it's a list of objects with 'question' key
        elif all(isinstance(item, dict) and 'question' in item for item in data):
            return [item['question'] for item in data]
        else:
            raise ValueError("Unsupported JSON structure for questions")
    elif isinstance(data, dict):
        # If it's a dict with 'questions' key
        if 'questions' in data:
            questions = data['questions']
            if isinstance(questions, list):
                if all(isinstance(item, str) for item in questions):
                    return questions
                elif all(isinstance(item, dict) and 'question' in item for item in questions):
                    return [item['question'] for item in questions]
        raise ValueError("Unsupported JSON structure for questions")
    else:
        raise ValueError("Questions file must contain a list or dict with questions")
