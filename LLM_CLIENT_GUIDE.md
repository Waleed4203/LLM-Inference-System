# LLM Client SDK - Direct Ollama Integration

A simple, importable Python client for LLM inference - works like OpenAI/Gemini SDKs.
**No queue, no Redis, no Celery** - just direct API calls.

## Files

| File | Purpose |
|------|---------|
| `llm_client.py` | Full-featured SDK with classes and utilities |
| `ai_helper.py` | Minimal single-file helper (copy to other projects) |
| `llm_client_examples.py` | Usage examples |

## Quick Start

### Option 1: Simple Helper (Recommended for most projects)

Copy `ai_helper.py` to your project and use:

```python
from ai_helper import ask, code, analyze, summarize

# Ask anything
answer = ask("What is Python?")

# Generate code
snippet = code("Write a function to validate emails")

# Analyze data/logs
result = analyze(error_log)

# Summarize text
summary = summarize(long_document)
```

### Option 2: Full SDK

```python
from llm_client import LLM, chat, generate

# Quick one-liner
response = chat("What is Python?")

# With system prompt
response = chat("Explain recursion", system="You are a coding tutor")

# Full control
llm = LLM(
    model="qwen2.5-coder:14b",
    system_prompt="You are a senior developer",
    temperature=0.3,
    max_tokens=4096,
)
response = llm.chat("How do I implement a binary tree?")
print(response.content)
print(f"Tokens: {response.usage.total_tokens}")
```

## Configuration

Edit the top of `ai_helper.py` or `llm_client.py`:

```python
OLLAMA_URL = "http://localhost:11434"  # Your Ollama server
DEFAULT_MODEL = "qwen2.5-coder:14b"    # Your preferred model
DEFAULT_TIMEOUT = 120                   # Request timeout
```

## Features

### Streaming

```python
from llm_client import LLM

llm = LLM()
for chunk in llm.stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### Conversation with Context

```python
llm = LLM(system_prompt="You are helpful")

history = []

# Turn 1
response = llm.chat("What is Python?", context=history)
history.append({"role": "user", "content": "What is Python?"})
history.append({"role": "assistant", "content": response.content})

# Turn 2 - remembers context
response = llm.chat("Show me an example", context=history)
```

### Pre-configured Clients

```python
from llm_client import create_coder, create_assistant

coder = create_coder()  # Low temp, code-focused
response = coder.chat("Write a sorting algorithm")

assistant = create_assistant()  # General purpose
response = assistant.chat("What's the weather?")
```

### Error Handling

```python
from llm_client import LLM, ConnectionError, ModelNotFoundError

try:
    llm = LLM()
    response = llm.chat("Hello")
except ConnectionError:
    print("Ollama not running!")
except ModelNotFoundError:
    print("Model not found!")
```

## Integration Pattern

For your projects, create a wrapper:

```python
# my_project/ai.py
from ai_helper import ask, code, analyze

def review_pr(diff: str) -> str:
    return analyze(diff, focus="code quality, bugs, security")

def generate_tests(code: str) -> str:
    return code(f"Write unit tests for:\n{code}")

def explain_error(error: str) -> str:
    return ask("What does this error mean and how to fix it?", context=error)
```

Then use anywhere:

```python
from my_project.ai import review_pr, generate_tests

feedback = review_pr(git_diff)
tests = generate_tests(my_function)
```

## Requirements

- Python 3.8+
- `requests` library (already in your requirements.txt)
- Ollama running locally or on a server

## Available Models

Check what's available:

```python
from llm_client import LLM
print(LLM().list_models())
```

Your current models:
- `qwen2.5-coder:14b` (default)
- `qwen3:14b`
- `codellama:13b`
- `codellama:34b`
- `deepseek-coder:33b`
- `llava:13b`
