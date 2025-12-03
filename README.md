# LLM Inference System

A robust, queue-based LLM inference system designed for reliable multi-user access with comprehensive logging and monitoring. Built with FastAPI, Celery, and Redis following production-grade best practices.

## 🌟 Features

- **Queue-Based Processing**: Handles concurrent requests without GPU overload
- **Asynchronous Architecture**: Submit requests and retrieve results independently
- **Disconnect-Resilient**: Tasks continue processing even if client disconnects
- **Comprehensive Logging**: Track queue wait time, processing time, and performance metrics
- **Error Handling**: Detailed error messages and exception tracebacks
- **GPU Support**: Optimized for NVIDIA GPUs with quantization support
- **API Key Authentication**: Secure access control
- **RESTful API**: Easy integration with any client
- **Monitoring**: Optional Flower dashboard for Celery monitoring

## 📋 Requirements

### Hardware
- **GPU**: NVIDIA RTX 3060 (12GB VRAM) or better (optional, can run on CPU)
- **RAM**: 16GB+ recommended
- **Storage**: 20GB+ for models

### Software
- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.9 or higher
- **Redis**: 6.0 or higher
- **CUDA**: 11.8+ (for GPU support)

## 🚀 Installation

### 1. Clone or Download

```bash
cd "c:\Users\Waleed\PycharmProjects\LLM Inference System"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Redis

**Option A: Docker (Recommended)**
```bash
docker-compose up -d redis
```

**Option B: Windows Native**
- Download Redis from: https://github.com/microsoftarchive/redis/releases
- Install and start Redis service

**Option C: WSL (Windows Subsystem for Linux)**
```bash
wsl
sudo apt-get update
sudo apt-get install redis-server
sudo service redis-server start
```

### 5. Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Important Settings**:
```env
# Set your API keys (comma-separated)
API_KEYS=your-secret-key-1,your-secret-key-2

# Model configuration (adjust for your GPU)
MODEL_NAME=gpt2  # Start with small model for testing
MODEL_DEVICE=cuda  # or 'cpu' if no GPU
USE_QUANTIZATION=true  # Recommended for larger models

# Redis (if not using defaults)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🎯 Running the System

### Step 1: Start Redis

If using Docker:
```bash
docker-compose up -d redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Step 2: Start Celery Worker

Open a terminal and run:

```bash
# Activate virtual environment
venv\Scripts\activate

# Start Celery worker
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Note**: On Windows, use `--pool=solo`. On Linux/Mac, you can use `--pool=prefork`.

The worker will:
1. Connect to Redis
2. Load the LLM model into GPU/CPU
3. Wait for tasks

**Expected Output**:
```
[INFO] Loading model: gpt2
[INFO] Device: cuda
[INFO] Model loaded successfully on cuda
[INFO] celery@hostname ready.
```

### Step 3: Start FastAPI Server

Open a **new terminal** and run:

```bash
# Activate virtual environment
venv\Scripts\activate

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 4: Test Locally

Open browser to: http://localhost:8000/docs

Or test with curl:

```bash
# Health check
curl http://localhost:8000/health

# Submit generation request
curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: your-secret-key-1" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Hello, how are you?\"}"

# Response: {"status": "queued", "task_id": "abc-123-def", "message": "..."}

# Get result
curl http://localhost:8000/result/abc-123-def \
  -H "X-API-Key: your-secret-key-1"
```

### Step 5: Expose with ngrok (Optional)

For remote access:

```bash
# Install ngrok: https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000
```

**Output**:
```
Forwarding  https://xxxx-xx-xx-xx-xx.ngrok.io -> http://localhost:8000
```

Use the ngrok URL for remote access:
```bash
curl https://xxxx-xx-xx-xx-xx.ngrok.io/health
```

## 📡 API Usage

### Authentication

All endpoints (except `/` and `/health`) require an API key:

```bash
-H "X-API-Key: your-secret-key-here"
```

### Endpoints

#### 1. Submit Generation Request

```bash
POST /generate
```

**Request**:
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "max_tokens": 512,
  "temperature": 0.7,
  "top_p": 0.9,
  "user_id": "user123"
}
```

**Response** (202 Accepted):
```json
{
  "status": "queued",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Your request is being processed. Use the task_id to check status."
}
```

#### 2. Check Task Status

```bash
GET /status/{task_id}
```

**Response**:
```json
{
  "status": "processing",  // or "queued", "completed", "failed"
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task is currently being processed"
}
```

#### 3. Get Result

```bash
GET /result/{task_id}
```

**Response (Success)**:
```json
{
  "status": "completed",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": "Quantum computing is a type of computing that...",
  "metrics": {
    "queue_wait_time": 2.3,
    "processing_time": 5.8,
    "total_time": 8.1,
    "prompt_tokens": 50,
    "completion_tokens": 200,
    "tokens_per_second": 34.48
  }
}
```

**Response (Error)**:
```json
{
  "status": "error",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_message": "CUDA out of memory",
  "error_type": "RuntimeError"
}
```

**Response (Still Processing)** (202 Accepted):
```json
{
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task is currently being processed"
}
```

#### 4. Health Check

```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "redis_connected": true,
  "model_loaded": true,
  "version": "1.0.0"
}
```

### Python Client Example

```python
import requests
import time

API_URL = "http://localhost:8000"
API_KEY = "your-secret-key-1"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Submit request
response = requests.post(
    f"{API_URL}/generate",
    headers=headers,
    json={
        "prompt": "Write a short poem about AI",
        "max_tokens": 256,
        "temperature": 0.8
    }
)

task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# Poll for result
while True:
    result = requests.get(
        f"{API_URL}/result/{task_id}",
        headers=headers
    )
    
    data = result.json()
    
    if data["status"] == "completed":
        print(f"\nResult: {data['result']}")
        print(f"\nMetrics: {data['metrics']}")
        break
    elif data["status"] == "error":
        print(f"\nError: {data['error_message']}")
        break
    else:
        print(f"Status: {data['status']}... waiting")
        time.sleep(2)
```

## 📊 Monitoring & Logging

### Log Files

All logs are stored in the `logs/` directory:

#### 1. `llm_requests.log` - Request Metrics

Human-readable log of all requests:

```
[2025-11-21 15:30:45] task_id=abc-123 status=success prompt_tokens=50 completion_tokens=200 tokens_per_sec=34.48 queue_wait=2.30s processing_time=5.80s total_time=8.10s
[2025-11-21 15:31:12] task_id=def-456 status=error error_message="CUDA out of memory" queue_wait=0.50s processing_time=3.20s total_time=3.70s
```

**Metrics Explained**:
- `queue_wait`: Time spent waiting in queue before processing started
- `processing_time`: Actual inference time (model generation)
- `total_time`: End-to-end latency (queue + processing)
- `tokens_per_sec`: Generation speed

#### 2. `app.log` - Application Logs

General application logs (INFO, WARNING, ERROR):

```
2025-11-21 15:30:45 - app.main - INFO - Received generation request from user: user123
2025-11-21 15:30:45 - app.tasks.inference - INFO - Starting task abc-123
2025-11-21 15:30:51 - app.tasks.inference - INFO - Task abc-123 completed successfully
```

#### 3. `errors.log` - Error Tracebacks

Detailed error information with full stack traces:

```
================================================================================
[2025-11-21 15:31:12] ERROR - Task def-456 failed
Error Type: RuntimeError
Error Message: CUDA out of memory

Traceback:
  File "app/tasks/inference.py", line 245, in generate_text
    outputs = model.generate(**inputs, max_new_tokens=max_tokens)
  File "transformers/generation/utils.py", line 1234, in generate
    ...
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB...
================================================================================
```

### Flower Monitoring (Optional)

Start Flower for real-time Celery monitoring:

```bash
docker-compose up -d flower
```

Access at: http://localhost:5555

Features:
- Active tasks
- Worker status
- Task history
- Performance graphs

## 🌐 Internet Stability & Disconnect Handling

### How It Works

The system is designed to handle unstable internet connections:

1. **Submit Request**: Client sends POST to `/generate`
2. **Immediate Response**: Server returns `task_id` immediately (< 1 second)
3. **Task Queued**: Request is stored in Redis queue
4. **Client Can Disconnect**: Client can close connection, shut down, etc.
5. **Processing Continues**: Celery worker processes task regardless of client connection
6. **Result Stored**: Completed result saved in Redis (expires after 1 hour)
7. **Retrieve Later**: Client reconnects and calls `/result/{task_id}` to get result

### Example Scenario

```
User A (unstable connection):
1. Submit request → Get task_id: "abc-123"
2. Internet disconnects ❌
3. [Task processes in background on server]
4. Internet reconnects ✅
5. Call /result/abc-123 → Get completed result

User B (concurrent request):
1. Submit request → Get task_id: "def-456"
2. Task queued (User A's task is processing)
3. Wait in queue for ~10 seconds
4. Task starts processing
5. Poll /result/def-456 every 2 seconds
6. Get result when complete
```

### Best Practices

- **Poll Regularly**: Check `/result/{task_id}` every 1-3 seconds
- **Save task_id**: Store task_id locally to retrieve results later
- **Handle Timeouts**: Tasks timeout after 120 seconds by default
- **Retry Failed Requests**: Check error_message and retry if appropriate

## 🔧 Configuration

### Model Selection

Edit `.env`:

```env
# Small model (testing, fast)
MODEL_NAME=gpt2

# Medium model (7B parameters, RTX 3060)
MODEL_NAME=TheBloke/Llama-2-7B-Chat-GPTQ
USE_QUANTIZATION=true

# Large model (13B parameters, needs more VRAM)
MODEL_NAME=TheBloke/Llama-2-13B-Chat-GPTQ
USE_QUANTIZATION=true
```

### Task Timeout

```env
# Timeout in seconds (default: 120)
TASK_TIME_LIMIT=180
```

### Concurrency

```env
# Number of concurrent tasks (default: 1 for single GPU)
CELERY_CONCURRENCY=1
```

## 🐛 Troubleshooting

### Redis Connection Error

**Error**: `redis.exceptions.ConnectionError: Error 10061`

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# If not, start Redis
docker-compose up -d redis
# OR
sudo service redis-server start  # Linux
```

### CUDA Out of Memory

**Error**: `RuntimeError: CUDA out of memory`

**Solutions**:
1. Use smaller model: `MODEL_NAME=gpt2`
2. Enable quantization: `USE_QUANTIZATION=true`
3. Reduce max_tokens: `MAX_NEW_TOKENS=256`
4. Use CPU: `MODEL_DEVICE=cpu`

### Model Not Loading

**Error**: `ModelLoadError: Failed to load model`

**Solutions**:
1. Check model name is correct
2. Ensure internet connection (first download)
3. Check disk space (models are large)
4. Try smaller model first

### Worker Not Starting

**Error**: `ImportError` or `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### API Key Invalid

**Error**: `401 Unauthorized: Invalid API key`

**Solution**:
1. Check `.env` file has `API_KEYS` set
2. Ensure header is: `X-API-Key: your-key`
3. Restart FastAPI server after changing `.env`

## 📈 Performance Optimization

### For RTX 3060 (12GB VRAM)

**Recommended Settings**:
```env
MODEL_NAME=TheBloke/Llama-2-7B-Chat-GPTQ
MODEL_DEVICE=cuda
USE_QUANTIZATION=true
MAX_NEW_TOKENS=512
CELERY_CONCURRENCY=1
```

**Expected Performance**:
- Queue wait: < 1s (no concurrent requests)
- Processing time: 5-15s (depending on output length)
- Tokens/second: 20-50

### Scaling Up

For more users or faster processing:

1. **Multiple GPUs**: Run multiple workers on different GPUs
2. **Distributed Workers**: Run workers on multiple machines
3. **Load Balancer**: Use nginx to distribute API requests
4. **Larger Model**: Upgrade GPU for better quality

## 🔐 Security

### Production Deployment

1. **Change API Keys**: Use strong, random keys
2. **Enable HTTPS**: Use ngrok with auth or proper SSL
3. **Rate Limiting**: Add rate limiting middleware
4. **CORS**: Configure `allow_origins` in `main.py`
5. **Firewall**: Restrict Redis port (6379) access

### ngrok Authentication

```bash
# Add authentication to ngrok
ngrok http 8000 --basic-auth="username:password"
```

## 📚 Architecture

```
┌─────────────┐
│   Client    │
│  (Browser,  │
│   Python)   │
└──────┬──────┘
       │ HTTP/HTTPS
       │ (ngrok tunnel)
       ▼
┌─────────────────────┐
│   FastAPI Server    │
│  - Receive requests │
│  - Enqueue tasks    │
│  - Return task_id   │
└──────┬──────────────┘
       │
       │ Celery task
       ▼
┌─────────────────────┐
│   Redis Queue       │
│  - Store tasks      │
│  - Store results    │
└──────┬──────────────┘
       │
       │ Pull task
       ▼
┌─────────────────────┐
│  Celery Worker      │
│  - Load LLM model   │
│  - Run inference    │
│  - Log metrics      │
│  - Store result     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   GPU (RTX 3060)    │
│  - Model inference  │
└─────────────────────┘
```

## 📝 License

This project is provided as-is for educational and research purposes.

## 🤝 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review troubleshooting section
3. Check Celery worker output
4. Verify Redis is running

## 🎉 Quick Start Summary

```bash
# 1. Start Redis
docker-compose up -d redis

# 2. Start Celery Worker (Terminal 1)
venv\Scripts\activate
celery -A app.celery_app worker --loglevel=info --pool=solo

# 3. Start FastAPI Server (Terminal 2)
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. Test
curl http://localhost:8000/health

# 5. (Optional) Expose with ngrok
ngrok http 8000
```

**You're ready to go! 🚀**
