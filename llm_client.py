"""
LLM Client SDK - Direct Ollama Integration
==========================================
A simple, importable client for LLM inference - works like OpenAI/Gemini SDKs.
No queue, no Redis, no Celery - just direct API calls.

Usage:
------
    from llm_client import LLM, chat, generate
    
    # Quick one-liner
    response = chat("What is Python?")
    
    # With system prompt
    response = chat("Explain recursion", system="You are a helpful coding tutor")
    
    # Full control
    llm = LLM(
        model="qwen2.5-coder:14b",
        system_prompt="You are a senior Python developer",
        temperature=0.7
    )
    response = llm.chat("How do I implement a binary tree?")
    
    # Streaming
    for chunk in llm.stream("Write a poem about coding"):
        print(chunk, end="", flush=True)
"""

import requests
import json
from typing import Optional, Dict, Any, Generator, List, Union
from dataclasses import dataclass, field


# ============================================================================
# CONFIGURATION - Edit these defaults for your setup
# ============================================================================

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:14b"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TOP_P = 0.9
DEFAULT_TIMEOUT = 120  # seconds


# ============================================================================
# RESPONSE CLASSES
# ============================================================================

@dataclass
class Usage:
    """Token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class Message:
    """A chat message."""
    role: str
    content: str


@dataclass
class LLMResponse:
    """Response from LLM generation."""
    content: str
    model: str
    usage: Usage
    done: bool = True
    total_duration: float = 0.0  # seconds
    
    def __str__(self) -> str:
        return self.content
    
    def __repr__(self) -> str:
        return f"LLMResponse(content='{self.content[:50]}...', tokens={self.usage.total_tokens})"


# ============================================================================
# EXCEPTIONS
# ============================================================================

class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class ConnectionError(LLMError):
    """Cannot connect to Ollama server."""
    pass


class ModelNotFoundError(LLMError):
    """Requested model not available."""
    pass


class TimeoutError(LLMError):
    """Request timed out."""
    pass


# ============================================================================
# MAIN LLM CLIENT CLASS
# ============================================================================

class LLM:
    """
    LLM Client for direct Ollama inference.
    
    Example:
        llm = LLM(model="qwen2.5-coder:14b", system_prompt="You are helpful")
        response = llm.chat("Hello!")
        print(response.content)
    """
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        system_prompt: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        top_p: float = DEFAULT_TOP_P,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize LLM client.
        
        Args:
            model: Ollama model name (e.g., "qwen2.5-coder:14b", "llama3", "mistral")
            base_url: Ollama server URL
            system_prompt: Default system prompt for all requests
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            timeout: Request timeout in seconds
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.timeout = timeout
        self._conversation_history: List[Message] = []
    
    def chat(
        self,
        message: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        """
        Send a chat message and get a response.
        
        Args:
            message: User message
            system: System prompt (overrides default)
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            top_p: Override default top_p
            context: Previous conversation context [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            LLMResponse with content and usage stats
        """
        messages = []
        
        # Add system prompt
        sys_prompt = system or self.system_prompt
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return self._call_chat_api(
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            top_p=top_p or self.top_p,
        )
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
    ) -> LLMResponse:
        """
        Generate text from a raw prompt (no chat formatting).
        
        Args:
            prompt: Raw text prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            top_p: Override default top_p
            
        Returns:
            LLMResponse with content and usage stats
        """
        return self._call_generate_api(
            prompt=prompt,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            top_p=top_p or self.top_p,
        )
    
    def stream(
        self,
        message: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """
        Stream a chat response token by token.
        
        Args:
            message: User message
            system: System prompt
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Yields:
            String chunks as they arrive
        """
        messages = []
        
        sys_prompt = system or self.system_prompt
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})
        
        messages.append({"role": "user", "content": message})
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            }
        }
        
        try:
            with requests.post(url, json=payload, stream=True, timeout=self.timeout) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout}s")
    
    def _call_chat_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> LLMResponse:
        """Internal: Call Ollama chat API."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            content = data.get("message", {}).get("content", "")
            
            usage = Usage(
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                done=data.get("done", True),
                total_duration=data.get("total_duration", 0) / 1e9,
            )
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")
            raise LLMError(f"API error: {e.response.status_code} - {e.response.text}")
    
    def _call_generate_api(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> LLMResponse:
        """Internal: Call Ollama generate API."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            content = data.get("response", "")
            
            usage = Usage(
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage=usage,
                done=data.get("done", True),
                total_duration=data.get("total_duration", 0) / 1e9,
            )
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")
            raise LLMError(f"API error: {e.response.status_code} - {e.response.text}")
    
    def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m.get("name") for m in models]
        except Exception as e:
            raise LLMError(f"Failed to list models: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama server is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# ============================================================================
# CONVENIENCE FUNCTIONS - For quick one-liner usage
# ============================================================================

# Default client instance (lazy loaded)
_default_client: Optional[LLM] = None


def _get_default_client() -> LLM:
    """Get or create default client."""
    global _default_client
    if _default_client is None:
        _default_client = LLM()
    return _default_client


def chat(
    message: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Quick chat function - returns just the response text.
    
    Example:
        response = chat("What is Python?")
        response = chat("Explain this code", system="You are a code reviewer")
    """
    if model:
        client = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
    else:
        client = _get_default_client()
    
    result = client.chat(message, system=system, temperature=temperature, max_tokens=max_tokens)
    return result.content


def generate(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Quick generate function - returns just the response text.
    
    Example:
        response = generate("Complete this: The quick brown fox")
    """
    if model:
        client = LLM(model=model, temperature=temperature, max_tokens=max_tokens)
    else:
        client = _get_default_client()
    
    result = client.generate(prompt, temperature=temperature, max_tokens=max_tokens)
    return result.content


def stream_chat(
    message: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Quick streaming chat - yields response chunks.
    
    Example:
        for chunk in stream_chat("Tell me a story"):
            print(chunk, end="", flush=True)
    """
    if model:
        client = LLM(model=model)
    else:
        client = _get_default_client()
    
    yield from client.stream(message, system=system)


# ============================================================================
# SPECIALIZED CLIENTS - Pre-configured for common use cases
# ============================================================================

def create_coder(model: str = DEFAULT_MODEL) -> LLM:
    """Create a coding-focused LLM client."""
    return LLM(
        model=model,
        system_prompt=(
            "You are an expert programmer. Write clean, efficient, well-documented code. "
            "Follow best practices and explain your reasoning when helpful."
        ),
        temperature=0.3,  # Lower for more deterministic code
        max_tokens=4096,
    )


def create_assistant(model: str = DEFAULT_MODEL) -> LLM:
    """Create a general assistant LLM client."""
    return LLM(
        model=model,
        system_prompt="You are a helpful, friendly assistant. Be concise and accurate.",
        temperature=0.7,
        max_tokens=2048,
    )


def create_analyst(model: str = DEFAULT_MODEL) -> LLM:
    """Create a data analysis focused LLM client."""
    return LLM(
        model=model,
        system_prompt=(
            "You are a data analyst expert. Analyze data carefully, provide insights, "
            "and explain statistical concepts clearly."
        ),
        temperature=0.4,
        max_tokens=2048,
    )


# ============================================================================
# MAIN - Test the client
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("LLM Client SDK - Testing")
    print("=" * 60)
    
    # Check connection
    llm = LLM()
    
    if not llm.is_available():
        print("\n❌ Ollama is not running!")
        print("   Start it with: ollama serve")
        exit(1)
    
    print(f"\n✅ Connected to Ollama at {llm.base_url}")
    print(f"📦 Available models: {', '.join(llm.list_models())}")
    print(f"🎯 Using model: {llm.model}")
    
    # Test chat
    print("\n" + "-" * 60)
    print("Testing chat()...")
    response = llm.chat("Say 'Hello, World!' and nothing else.")
    print(f"Response: {response.content}")
    print(f"Tokens: {response.usage.total_tokens}")
    
    # Test with system prompt
    print("\n" + "-" * 60)
    print("Testing chat with system prompt...")
    response = llm.chat(
        "What's 2+2?",
        system="You are a math tutor. Always explain your answer."
    )
    print(f"Response: {response.content}")
    
    # Test streaming
    print("\n" + "-" * 60)
    print("Testing streaming...")
    print("Response: ", end="")
    for chunk in llm.stream("Count from 1 to 5"):
        print(chunk, end="", flush=True)
    print("\n")
    
    print("=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)
