# 🚀 Quick Start Guide

## Your API Keys
```
test-key-123
demo-key-456
```

## Base URL
```
http://localhost:8000
```

---

## 1️⃣ Start the System

### Option A: Use the batch file
```bash
.\setup_and_run.bat
```

Then open TWO terminals:

**Terminal 1:**
```bash
python -m celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Terminal 2:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option B: Use the start script
```bash
.\start.bat
```

---

## 2️⃣ Test the API

### Quick Test (Python)
```bash
python client_example.py
```

### Manual Test (cURL)
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Hello, how are you?\", \"max_tokens\": 100}"
```

---

## 3️⃣ Basic API Usage

### Step 1: Submit Request
```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    headers={"X-API-Key": "test-key-123"},
    json={"prompt": "Write a Python hello world"}
)

task_id = response.json()["task_id"]
```

### Step 2: Get Result
```python
result = requests.get(
    f"http://localhost:8000/result/{task_id}",
    headers={"X-API-Key": "test-key-123"}
)

print(result.json()["result"])
```

---

## 4️⃣ Use with Ollama (Recommended)

### Install Ollama
Download from: https://ollama.ai/download

### Pull a Model
```bash
ollama pull llama2
```

### Configure
Edit `.env`:
```env
MODEL_BACKEND=ollama
OLLAMA_MODEL=llama2
```

### Restart Services
Restart both Celery and FastAPI

---

## 📚 Full Documentation

- **API Docs:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Ollama Setup:** [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
- **Interactive Docs:** http://localhost:8000/docs

---

## 🔍 Check System Status

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "model_loaded": true,
  "backend": "ollama",
  "model": "llama2"
}
```

---

## 🎯 Common Use Cases

### Chat Completion
```python
client.generate(
    prompt="User: What is Python?\nAssistant:",
    max_tokens=256,
    temperature=0.7
)
```

### Code Generation
```python
client.generate(
    prompt="Write a function to sort a list in Python:",
    max_tokens=200,
    temperature=0.3
)
```

### Creative Writing
```python
client.generate(
    prompt="Write a short story about a robot:",
    max_tokens=500,
    temperature=1.0
)
```

---

## ⚡ Tips

1. **Lower temperature (0.3)** = More focused, deterministic
2. **Higher temperature (1.0)** = More creative, random
3. **Use Ollama** for faster local inference
4. **Check logs** in `logs/` folder for debugging
5. **Interactive docs** at http://localhost:8000/docs

---

## 🆘 Troubleshooting

### API not responding?
```bash
# Check if services are running
curl http://localhost:8000/health
```

### Ollama not working?
```bash
# Check Ollama is running
ollama list

# Start Ollama
ollama serve
```

### Redis not connected?
```bash
# Check Docker
docker ps

# Restart Redis
docker-compose up -d
```

---

## 📞 Need Help?

1. Check `logs/app.log` for errors
2. Visit http://localhost:8000/docs for interactive testing
3. Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for details
