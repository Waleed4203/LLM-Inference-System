# Quick Start Guide

## Prerequisites
1. **Start Docker Desktop** - Make sure Docker Desktop is running
2. Python 3.9+ installed ✓
3. Dependencies installed ✓

## Setup Steps

### 1. Start Docker & Redis
Run the setup script:
```bash
setup_and_run.bat
```

OR manually:
```bash
docker-compose up -d redis
```

### 2. Start Celery Worker (Terminal 1)
Open a terminal and run:
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### 3. Start FastAPI Server (Terminal 2)
Open another terminal and run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test the API
Visit: http://localhost:8000/docs

Or test with curl:
```bash
curl http://localhost:8000/health
```

## Configuration

The `.env` file has been created with default settings:
- Model: gpt2 (small, fast for testing)
- Device: CPU (change to cuda if you have GPU)
- API Keys: test-key-123, demo-key-456

To use a different model or GPU, edit the `.env` file.

## Troubleshooting

### Docker not running
- Start Docker Desktop application
- Wait for it to fully start (whale icon in system tray)
- Run `docker ps` to verify

### Redis connection error
```bash
# Check if Redis is running
docker ps

# Restart Redis if needed
docker-compose restart redis
```

### Module not found errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

Once everything is running:
1. Go to http://localhost:8000/docs
2. Try the `/generate` endpoint with your API key
3. Check logs in the `logs/` directory
4. Monitor with Flower (optional): `docker-compose up -d flower` then visit http://localhost:5555
