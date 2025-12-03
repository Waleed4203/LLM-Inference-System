"""
AI Helper - Copy this file to your other projects
=================================================
This is a minimal template you can drop into any Python project.
Just copy this single file and start using AI in your code.

Configuration:
- Edit OLLAMA_URL if your Ollama server is on a different machine
- Edit DEFAULT_MODEL to your preferred model
- Edit the system prompts in the helper functions as needed

Usage in your project:
    from ai_helper import ask, code, analyze, summarize
    
    # Quick question
    answer = ask("What is the capital of France?")
    
    # Generate code
    code_snippet = code("Write a function to sort a list")
    
    # Analyze something
    analysis = analyze("This error log shows...")
    
    # Summarize text
    summary = summarize(long_text)
"""

import requests
import json
from typing import Optional, Generator

# ============================================================================
# CONFIGURATION - EDIT THESE FOR YOUR SETUP
# ============================================================================

OLLAMA_URL = "http://localhost:11434"  # Change if Ollama is on another machine
DEFAULT_MODEL = "qwen2.5-coder:14b"    # Change to your preferred model
DEFAULT_TIMEOUT = 120                   # Seconds


# ============================================================================
# CORE FUNCTION - Everything else uses this
# ============================================================================

def _call_llm(
    prompt: str,
    system: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    stream: bool = False,
) -> str | Generator[str, None, None]:
    """
    Internal function to call Ollama API.
    """
    url = f"{OLLAMA_URL}/api/chat"
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
        }
    }
    
    try:
        if stream:
            def generate():
                with requests.post(url, json=payload, stream=True, timeout=DEFAULT_TIMEOUT) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
            return generate()
        else:
            response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
    except requests.exceptions.ConnectionError:
        return f"Error: Cannot connect to Ollama at {OLLAMA_URL}. Is it running?"
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================================================
# HELPER FUNCTIONS - Use these in your code
# ============================================================================

def ask(question: str, context: str = "") -> str:
    """
    Ask a general question.
    
    Example:
        answer = ask("What is recursion?")
        answer = ask("Explain this error", context=error_message)
    """
    prompt = question
    if context:
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
    
    return _call_llm(
        prompt=prompt,
        system="You are a helpful assistant. Be concise and accurate.",
        temperature=0.7,
    )


def code(request: str, language: str = "python") -> str:
    """
    Generate or explain code.
    
    Example:
        snippet = code("Write a function to validate emails")
        explanation = code("Explain what this does: def foo(): pass")
    """
    return _call_llm(
        prompt=request,
        system=f"You are an expert {language} programmer. Write clean, efficient, well-documented code. Only output code unless explanation is specifically requested.",
        temperature=0.3,
        max_tokens=4096,
    )


def analyze(data: str, focus: str = "") -> str:
    """
    Analyze data, logs, or text.
    
    Example:
        result = analyze(error_log)
        result = analyze(sales_data, focus="trends")
    """
    prompt = f"Analyze this:\n{data}"
    if focus:
        prompt += f"\n\nFocus on: {focus}"
    
    return _call_llm(
        prompt=prompt,
        system="You are a data analyst. Provide clear, actionable insights.",
        temperature=0.4,
    )


def summarize(text: str, max_length: str = "medium") -> str:
    """
    Summarize text.
    
    Example:
        summary = summarize(long_article)
        summary = summarize(document, max_length="short")
    """
    length_guide = {
        "short": "1-2 sentences",
        "medium": "1 paragraph",
        "long": "2-3 paragraphs",
    }
    
    return _call_llm(
        prompt=f"Summarize this in {length_guide.get(max_length, 'medium')}:\n\n{text}",
        system="You are a summarization expert. Be concise and capture key points.",
        temperature=0.3,
    )


def review_code(code_snippet: str) -> str:
    """
    Review code for issues.
    
    Example:
        feedback = review_code(my_function_code)
    """
    return _call_llm(
        prompt=f"Review this code for bugs, security issues, and improvements:\n\n```\n{code_snippet}\n```",
        system="You are a senior code reviewer. Be specific and constructive.",
        temperature=0.3,
    )


def translate(text: str, target_language: str) -> str:
    """
    Translate text to another language.
    
    Example:
        spanish = translate("Hello world", "Spanish")
    """
    return _call_llm(
        prompt=f"Translate to {target_language}:\n\n{text}",
        system="You are a professional translator. Provide accurate, natural translations.",
        temperature=0.3,
    )


def chat_stream(message: str, system: str = "You are a helpful assistant.") -> Generator[str, None, None]:
    """
    Stream a response token by token.
    
    Example:
        for chunk in chat_stream("Tell me a story"):
            print(chunk, end="", flush=True)
    """
    return _call_llm(
        prompt=message,
        system=system,
        stream=True,
    )


def is_available() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def list_models() -> list:
    """List available models."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        return [m.get("name") for m in response.json().get("models", [])]
    except:
        return []


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("AI Helper - Testing Connection")
    print("=" * 40)
    
    if is_available():
        print(f"✅ Connected to Ollama at {OLLAMA_URL}")
        print(f"📦 Models: {list_models()}")
        print(f"🎯 Using: {DEFAULT_MODEL}")
        
        print("\nTest query...")
        response = ask("Say 'Hello!' and nothing else")
        print(f"Response: {response}")
    else:
        print(f"❌ Cannot connect to Ollama at {OLLAMA_URL}")
        print("   Make sure Ollama is running: ollama serve")
