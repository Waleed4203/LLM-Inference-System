# LLM Inference System - API Documentation

## 🔑 Authentication

All API requests require an API key in the header:

```
X-API-Key: your-api-key-here
```

### Your API Keys (from .env)
- `test-key-123`
- `demo-key-456`

You can add more keys in `.env`:
```env
API_KEYS=test-key-123,demo-key-456,your-custom-key
```

---

## 📡 Base URL

```
http://localhost:8000
```

---

## 🚀 API Endpoints

### 1. Health Check
Check if the system is running and ready.

**Endpoint:** `GET /health`

**No authentication required**

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "redis_connected": true,
  "model_loaded": true,
  "version": "1.0.0",
  "backend": "ollama",
  "model": "llama2",
  "available_models": ["llama2", "mistral"]
}
```

---

### 2. Generate Text (Submit Request)
Submit a text generation request. Returns immediately with a task ID.

**Endpoint:** `POST /generate`

**Headers:**
```
X-API-Key: test-key-123
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "Your prompt here",
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9,
  "user_id": "optional-user-id"
}
```

**Parameters:**
- `prompt` (required): Your input text
- `max_tokens` (optional): Maximum tokens to generate (default: 512)
- `temperature` (optional): Sampling temperature 0.0-2.0 (default: 0.7)
- `top_p` (optional): Nucleus sampling 0.0-1.0 (default: 0.9)
- `user_id` (optional): Your user identifier for tracking

**Example:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to reverse a string",
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

**Response:**
```json
{
  "status": "queued",
  "task_id": "abc123-def456-ghi789",
  "message": "Your request is being processed. Use the task_id to check status."
}
```

---

### 3. Check Status
Check if your request is still processing or completed.

**Endpoint:** `GET /status/{task_id}`

**Headers:**
```
X-API-Key: test-key-123
```

**Example:**
```bash
curl -X GET "http://localhost:8000/status/abc123-def456-ghi789" \
  -H "X-API-Key: test-key-123"
```

**Response:**
```json
{
  "status": "processing",
  "task_id": "abc123-def456-ghi789",
  "message": "Task is currently being processed"
}
```

**Status Values:**
- `queued` - Waiting in queue
- `processing` - Currently generating
- `completed` - Finished successfully
- `failed` - Error occurred

---

### 4. Get Result
Retrieve the generated text and metrics.

**Endpoint:** `GET /result/{task_id}`

**Headers:**
```
X-API-Key: test-key-123
```

**Example:**
```bash
curl -X GET "http://localhost:8000/result/abc123-def456-ghi789" \
  -H "X-API-Key: test-key-123"
```

**Response (Success):**
```json
{
  "status": "completed",
  "task_id": "abc123-def456-ghi789",
  "result": "Here is a Python function to reverse a string:\n\ndef reverse_string(s):\n    return s[::-1]",
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

**Response (Still Processing):**
```json
{
  "status": "processing",
  "task_id": "abc123-def456-ghi789",
  "message": "Task is currently being processed"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "task_id": "abc123-def456-ghi789",
  "error_message": "Model loading failed",
  "error_type": "ModelLoadError"
}
```

---

### 5. Stream Progress (SSE)
Get real-time updates using Server-Sent Events.

**Endpoint:** `GET /stream/{task_id}`

**Headers:**
```
X-API-Key: test-key-123
```

**Example (JavaScript):**
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/stream/abc123-def456-ghi789?api_key=test-key-123'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.status, data.message);
  
  if (data.status === 'completed') {
    console.log('Result:', data.result);
    eventSource.close();
  }
};
```

---

### 6. Metrics (Prometheus)
Get system metrics for monitoring.

**Endpoint:** `GET /metrics`

**No authentication required**

**Example:**
```bash
curl http://localhost:8000/metrics
```

---

## 💻 Code Examples

### Python (Simple)
```python
import requests
import time

API_KEY = "test-key-123"
BASE_URL = "http://localhost:8000"

# Submit request
response = requests.post(
    f"{BASE_URL}/generate",
    headers={"X-API-Key": API_KEY},
    json={
        "prompt": "Explain machine learning in simple terms",
        "max_tokens": 256,
        "temperature": 0.7
    }
)

task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# Poll for result
while True:
    result = requests.get(
        f"{BASE_URL}/result/{task_id}",
        headers={"X-API-Key": API_KEY}
    ).json()
    
    if result["status"] == "completed":
        print("\nResult:", result["result"])
        print("\nMetrics:", result["metrics"])
        break
    elif result["status"] == "error":
        print("Error:", result["error_message"])
        break
    else:
        print(f"Status: {result['status']}...")
        time.sleep(2)
```

### Python (Using Client Class)
```python
from client_example import LLMClient

# Initialize client
client = LLMClient(
    base_url="http://localhost:8000",
    api_key="test-key-123"
)

# Generate text (waits for result)
result = client.generate(
    prompt="Write a haiku about programming",
    max_tokens=100,
    temperature=0.8,
    wait=True
)

print(result["result"])
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

const API_KEY = 'test-key-123';
const BASE_URL = 'http://localhost:8000';

async function generateText(prompt) {
  // Submit request
  const submitResponse = await axios.post(
    `${BASE_URL}/generate`,
    {
      prompt: prompt,
      max_tokens: 256,
      temperature: 0.7
    },
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );
  
  const taskId = submitResponse.data.task_id;
  console.log('Task ID:', taskId);
  
  // Poll for result
  while (true) {
    const resultResponse = await axios.get(
      `${BASE_URL}/result/${taskId}`,
      {
        headers: { 'X-API-Key': API_KEY }
      }
    );
    
    const result = resultResponse.data;
    
    if (result.status === 'completed') {
      console.log('\nResult:', result.result);
      console.log('\nMetrics:', result.metrics);
      break;
    } else if (result.status === 'error') {
      console.error('Error:', result.error_message);
      break;
    } else {
      console.log(`Status: ${result.status}...`);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

generateText('Explain quantum computing in simple terms');
```

### cURL (Complete Flow)
```bash
# 1. Submit request
TASK_ID=$(curl -s -X POST "http://localhost:8000/generate" \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a joke about AI", "max_tokens": 100}' \
  | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# 2. Check status
curl -X GET "http://localhost:8000/status/$TASK_ID" \
  -H "X-API-Key: test-key-123"

# 3. Get result (wait a few seconds first)
sleep 5
curl -X GET "http://localhost:8000/result/$TASK_ID" \
  -H "X-API-Key: test-key-123"
```

---

## 🔒 Rate Limiting

- **60 requests per minute** per API key
- **Burst size:** 10 requests

If you exceed the limit, you'll get:
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429
}
```

---

## ⚙️ Configuration

### Change API Keys
Edit `.env`:
```env
API_KEYS=your-key-1,your-key-2,your-key-3
```

### Change Model Backend
```env
# Use Ollama (local)
MODEL_BACKEND=ollama
OLLAMA_MODEL=llama2

# Or use Transformers (Hugging Face)
MODEL_BACKEND=transformers
MODEL_NAME=gpt2
```

### Adjust Generation Defaults
```env
MAX_NEW_TOKENS=512
TEMPERATURE=0.7
TASK_TIME_LIMIT=120
```

---

## 📊 Response Times

Typical response times (depends on model and hardware):

| Model | Hardware | Tokens/sec | 256 tokens |
|-------|----------|------------|------------|
| GPT-2 | CPU | 10-20 | ~15s |
| Llama 2 7B | CPU | 2-5 | ~60s |
| Llama 2 7B | GPU | 20-50 | ~8s |
| Mistral 7B | GPU | 30-60 | ~5s |

---

## 🐛 Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 202 | Accepted (task queued) |
| 400 | Bad request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 404 | Task not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## 📝 Interactive API Docs

Visit these URLs when the server is running:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide interactive API testing directly in your browser!

---

## 🧪 Testing

Use the included test client:
```bash
python client_example.py
```

Or run the test suite:
```bash
pytest tests/
```

---

## 🔧 Advanced Usage

### Custom User Tracking
```python
response = requests.post(
    f"{BASE_URL}/generate",
    headers={"X-API-Key": API_KEY},
    json={
        "prompt": "Your prompt",
        "user_id": "user-12345"  # Track by user
    }
)
```

### Adjust Temperature for Creativity
```python
# More creative (random)
{"temperature": 1.2}

# More focused (deterministic)
{"temperature": 0.3}
```

### Control Output Length
```python
# Short response
{"max_tokens": 50}

# Long response
{"max_tokens": 1000}
```

---

## 📞 Support

- Check logs: `logs/app.log`
- Request logs: `logs/llm_requests.log`
- Error logs: `logs/errors.log`
- Health check: `GET /health`
- Metrics: `GET /metrics`
