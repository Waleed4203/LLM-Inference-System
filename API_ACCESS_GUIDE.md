# 🔑 API Access Guide - Everything You Need

## Your Credentials

### API Keys (Already Configured)
```
test-key-123
demo-key-456
```

### API Base URL
```
http://localhost:8000
```

### Add More API Keys
Edit `.env` file:
```env
API_KEYS=test-key-123,demo-key-456,your-new-key,another-key
```

---

## 🎯 How to Use the API

### Method 1: Python Client (Easiest)

```python
from client_example import LLMClient

# Initialize
client = LLMClient(
    base_url="http://localhost:8000",
    api_key="test-key-123"
)

# Generate text
result = client.generate(
    prompt="Your prompt here",
    max_tokens=256,
    temperature=0.7,
    wait=True  # Waits for result
)

print(result["result"])
```

**Run it:**
```bash
python client_example.py
```

---

### Method 2: Python Requests

```python
import requests
import time

API_KEY = "test-key-123"
BASE_URL = "http://localhost:8000"

# Step 1: Submit request
response = requests.post(
    f"{BASE_URL}/generate",
    headers={"X-API-Key": API_KEY},
    json={
        "prompt": "Explain AI in simple terms",
        "max_tokens": 256
    }
)

task_id = response.json()["task_id"]

# Step 2: Wait and get result
while True:
    result = requests.get(
        f"{BASE_URL}/result/{task_id}",
        headers={"X-API-Key": API_KEY}
    ).json()
    
    if result["status"] == "completed":
        print(result["result"])
        break
    
    time.sleep(2)
```

---

### Method 3: cURL

```bash
# Submit request
curl -X POST "http://localhost:8000/generate" \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world", "max_tokens": 100}'

# Get result (use task_id from above)
curl -X GET "http://localhost:8000/result/YOUR_TASK_ID" \
  -H "X-API-Key: test-key-123"
```

---

### Method 4: Postman

1. Import `LLM_API.postman_collection.json`
2. Set variables:
   - `base_url`: http://localhost:8000
   - `api_key`: test-key-123
3. Run requests in order:
   - Health Check
   - Generate Text
   - Get Result

---

### Method 5: JavaScript/Node.js

```javascript
const axios = require('axios');

const API_KEY = 'test-key-123';
const BASE_URL = 'http://localhost:8000';

async function generate(prompt) {
  // Submit
  const { data } = await axios.post(
    `${BASE_URL}/generate`,
    { prompt, max_tokens: 256 },
    { headers: { 'X-API-Key': API_KEY } }
  );
  
  const taskId = data.task_id;
  
  // Poll for result
  while (true) {
    const result = await axios.get(
      `${BASE_URL}/result/${taskId}`,
      { headers: { 'X-API-Key': API_KEY } }
    );
    
    if (result.data.status === 'completed') {
      return result.data.result;
    }
    
    await new Promise(r => setTimeout(r, 2000));
  }
}

generate('Explain quantum computing').then(console.log);
```

---

## 📋 All API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Check system status |
| `/generate` | POST | Yes | Submit generation request |
| `/status/{task_id}` | GET | Yes | Check task status |
| `/result/{task_id}` | GET | Yes | Get generated text |
| `/stream/{task_id}` | GET | Yes | Stream progress (SSE) |
| `/metrics` | GET | No | Prometheus metrics |
| `/docs` | GET | No | Interactive API docs |

---

## 🔐 Authentication

All requests (except `/health`, `/metrics`, `/docs`) require:

**Header:**
```
X-API-Key: test-key-123
```

**Example:**
```python
headers = {"X-API-Key": "test-key-123"}
```

---

## 📝 Request Parameters

### Generate Request Body

```json
{
  "prompt": "Your text here",           // Required
  "max_tokens": 512,                    // Optional (default: 512)
  "temperature": 0.7,                   // Optional (default: 0.7)
  "top_p": 0.9,                         // Optional (default: 0.9)
  "user_id": "optional-user-id"         // Optional
}
```

**Parameter Guide:**
- `prompt`: Your input text
- `max_tokens`: Max length of response (50-2000)
- `temperature`: Creativity (0.0 = focused, 2.0 = random)
- `top_p`: Diversity (0.0-1.0, usually 0.9)
- `user_id`: Track requests by user

---

## 📊 Response Format

### Success Response
```json
{
  "status": "completed",
  "task_id": "abc-123",
  "result": "Generated text here...",
  "metrics": {
    "queue_wait_time": 0.5,
    "processing_time": 2.3,
    "total_time": 2.8,
    "prompt_tokens": 12,
    "completion_tokens": 45,
    "tokens_per_second": 19.57
  }
}
```

### Error Response
```json
{
  "status": "error",
  "task_id": "abc-123",
  "error_message": "Description of error",
  "error_type": "ModelLoadError"
}
```

---

## 🎨 Use Cases & Examples

### 1. Code Generation
```python
client.generate(
    prompt="Write a Python function to calculate fibonacci",
    max_tokens=200,
    temperature=0.3  # Lower = more focused
)
```

### 2. Question Answering
```python
client.generate(
    prompt="Q: What is the capital of France?\nA:",
    max_tokens=50,
    temperature=0.2
)
```

### 3. Creative Writing
```python
client.generate(
    prompt="Write a poem about the ocean",
    max_tokens=300,
    temperature=1.0  # Higher = more creative
)
```

### 4. Chat Completion
```python
client.generate(
    prompt="User: How do I learn Python?\nAssistant:",
    max_tokens=256,
    temperature=0.7
)
```

### 5. Text Summarization
```python
client.generate(
    prompt="Summarize this text: [your long text here]",
    max_tokens=150,
    temperature=0.5
)
```

---

## ⚙️ Configuration

### Current Setup (from .env)

```env
# API Keys
API_KEYS=test-key-123,demo-key-456

# Backend (ollama or transformers)
MODEL_BACKEND=ollama
OLLAMA_MODEL=llama2

# Server
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Rate Limiting
60 requests/minute per API key
```

### Change Model

**Use Ollama (Recommended):**
```env
MODEL_BACKEND=ollama
OLLAMA_MODEL=llama2
```

**Use Transformers:**
```env
MODEL_BACKEND=transformers
MODEL_NAME=gpt2
```

---

## 🚀 Getting Started (3 Steps)

### Step 1: Start Services
```bash
# Terminal 1
python -m celery -A app.celery_app worker --loglevel=info --pool=solo

# Terminal 2
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Test Health
```bash
curl http://localhost:8000/health
```

### Step 3: Generate Text
```bash
python client_example.py
```

---

## 🌐 Interactive Testing

Visit these URLs in your browser:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Both provide interactive API testing without code!

---

## 📈 Monitoring

### Check Logs
```bash
# Application logs
type logs\app.log

# Request logs
type logs\llm_requests.log

# Error logs
type logs\errors.log
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics
```

---

## 🔧 Troubleshooting

### "Unauthorized" Error
- Check your API key is correct
- Ensure header is `X-API-Key` (case-sensitive)

### "Rate limit exceeded"
- Wait 1 minute
- Or add more API keys in `.env`

### "Connection refused"
- Check server is running: `curl http://localhost:8000/health`
- Restart FastAPI server

### Slow responses
- Use Ollama instead of Transformers
- Use smaller model (e.g., `phi` instead of `llama2`)
- Use GPU if available

---

## 📚 Documentation Files

- **This file:** Complete API access guide
- **API_DOCUMENTATION.md:** Detailed API reference
- **QUICK_START.md:** Quick setup guide
- **OLLAMA_SETUP.md:** Ollama integration guide
- **LLM_API.postman_collection.json:** Postman collection

---

## 💡 Pro Tips

1. **Use lower temperature (0.3)** for factual/code tasks
2. **Use higher temperature (1.0)** for creative tasks
3. **Start with Ollama + llama2** for best experience
4. **Check `/docs`** for interactive testing
5. **Monitor `/metrics`** for performance tracking
6. **Use `user_id`** to track usage per user
7. **Poll `/result`** every 2-3 seconds
8. **Check logs** if something goes wrong

---

## 🎯 Quick Reference

```python
# Import
from client_example import LLMClient

# Initialize
client = LLMClient("http://localhost:8000", "test-key-123")

# Generate
result = client.generate("Your prompt", wait=True)
print(result["result"])
```

That's it! You're ready to use the API. 🚀
