# Ollama Integration Guide

This system now supports **Ollama** as a backend, allowing you to use local LLM models just like calling OpenAI or Gemini APIs!

## Quick Start

### 1. Install Ollama

Download and install Ollama from: https://ollama.ai/download

For Windows, download the installer and run it.

### 2. Pull a Model

Open a terminal and pull a model (e.g., Llama 2):

```bash
ollama pull llama2
```

Other popular models:
- `ollama pull mistral` - Mistral 7B
- `ollama pull codellama` - Code Llama
- `ollama pull llama2:13b` - Llama 2 13B
- `ollama pull phi` - Microsoft Phi-2

### 3. Verify Ollama is Running

```bash
ollama list
```

This should show your installed models.

### 4. Configure the System

Edit your `.env` file:

```env
# Set backend to ollama
MODEL_BACKEND=ollama

# Configure which Ollama model to use
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### 5. Restart Services

Stop and restart both Celery worker and FastAPI server:

**Terminal 1 - Celery Worker:**
```bash
python -m celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Terminal 2 - FastAPI Server:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Test the API

```bash
python client_example.py
```

Or use curl:

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

## API Usage

The API works exactly like OpenAI or Gemini:

### Submit Request
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    headers={"X-API-Key": "test-key-123"},
    json={
        "prompt": "Write a Python function to calculate fibonacci",
        "max_tokens": 512,
        "temperature": 0.7
    }
)

task_id = response.json()["task_id"]
```

### Get Result
```python
result = requests.get(
    f"http://localhost:8000/result/{task_id}",
    headers={"X-API-Key": "test-key-123"}
)

print(result.json()["result"])
```

## Switching Between Backends

### Use Ollama (Local Models)
```env
MODEL_BACKEND=ollama
OLLAMA_MODEL=llama2
```

### Use Transformers (Hugging Face Models)
```env
MODEL_BACKEND=transformers
MODEL_NAME=gpt2
MODEL_DEVICE=cpu
```

## Available Ollama Models

Check available models:
```bash
ollama list
```

Popular models:
- **llama2** - Meta's Llama 2 (7B)
- **mistral** - Mistral 7B
- **codellama** - Code-specialized Llama
- **phi** - Microsoft Phi-2 (2.7B, fast)
- **neural-chat** - Intel's Neural Chat
- **starling-lm** - Starling LM 7B

## Benefits of Ollama

✅ **No GPU Required** - Runs on CPU (though GPU is faster)
✅ **Privacy** - All processing happens locally
✅ **No API Keys** - No external API costs
✅ **Fast** - Optimized for local inference
✅ **Easy Model Management** - Simple `ollama pull` command

## Troubleshooting

### Ollama not connecting?
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service (if needed)
ollama serve
```

### Model not found?
```bash
# Pull the model first
ollama pull llama2
```

### Check health endpoint
```bash
curl http://localhost:8000/health
```

Should show:
```json
{
  "status": "healthy",
  "backend": "ollama",
  "model": "llama2",
  "available_models": ["llama2", "mistral", ...]
}
```
