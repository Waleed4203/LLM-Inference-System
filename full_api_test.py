"""
Full API Flow Test Script
Tests all endpoints: health, generate, status, result
"""
import requests
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-key-123"  # From .env file

def print_separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)

def test_health():
    """Step 1: Test health endpoint (no auth required)"""
    print_separator("STEP 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Status: {data.get('status')}")
        print(f"✓ Redis Connected: {data.get('redis_connected')}")
        print(f"✓ Model Loaded: {data.get('model_loaded')}")
        print(f"✓ Model Backend: {data.get('model_backend', 'N/A')}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - Is the server running?")
        print("  Start with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_generate(prompt):
    """Step 2: Submit a generation request"""
    print_separator("STEP 2: Submit Generation Request")
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.7,
        "top_p": 0.9
    }
    
    try:
        print(f"Prompt: {prompt}")
        response = requests.post(
            f"{BASE_URL}/generate",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        task_id = data.get("task_id")
        print(f"✓ Request submitted successfully!")
        print(f"✓ Task ID: {task_id}")
        print(f"✓ Status: {data.get('status')}")
        print(f"✓ Position in Queue: {data.get('position', 'N/A')}")
        return task_id
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e}")
        print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_status(task_id):
    """Step 3: Check task status"""
    print_separator("STEP 3: Check Task Status")
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(
            f"{BASE_URL}/status/{task_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        print(f"✓ Task ID: {data.get('task_id')}")
        print(f"✓ Status: {data.get('status')}")
        print(f"✓ Created At: {data.get('created_at', 'N/A')}")
        return data.get("status")
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_result(task_id, max_wait=120):
    """Step 4: Poll for and get the result"""
    print_separator("STEP 4: Wait for Result")
    headers = {"X-API-Key": API_KEY}
    
    start_time = time.time()
    poll_count = 0
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait:
            print(f"\n✗ Timeout after {max_wait}s")
            return None
        
        try:
            response = requests.get(
                f"{BASE_URL}/result/{task_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            
            poll_count += 1
            print(f"  Poll #{poll_count}: Status = {status} ({elapsed:.1f}s elapsed)", end='\r')
            
            if status == "completed":
                print(f"\n✓ Task completed after {elapsed:.1f}s!")
                return data
            elif status == "error":
                print(f"\n✗ Task failed: {data.get('error_message')}")
                return data
            else:
                time.sleep(2)  # Poll every 2 seconds
                
        except Exception as e:
            print(f"\n✗ Error polling: {e}")
            time.sleep(2)

def display_result(result):
    """Display the final result"""
    print_separator("FINAL RESULT")
    
    if result.get("status") == "completed":
        print("\n📄 Generated Text:")
        print("-" * 40)
        print(result.get("result", "No result"))
        print("-" * 40)
        
        metrics = result.get("metrics", {})
        if metrics:
            print("\n📊 Performance Metrics:")
            print(f"  • Queue Wait Time:   {metrics.get('queue_wait_time', 0):.2f}s")
            print(f"  • Processing Time:   {metrics.get('processing_time', 0):.2f}s")
            print(f"  • Total Time:        {metrics.get('total_time', 0):.2f}s")
            print(f"  • Prompt Tokens:     {metrics.get('prompt_tokens', 0)}")
            print(f"  • Completion Tokens: {metrics.get('completion_tokens', 0)}")
            print(f"  • Tokens/Second:     {metrics.get('tokens_per_second', 0):.2f}")
    else:
        print(f"✗ Error: {result.get('error_message', 'Unknown error')}")
        print(f"  Error Type: {result.get('error_type', 'Unknown')}")

def test_metrics():
    """Bonus: Test metrics endpoint"""
    print_separator("BONUS: Prometheus Metrics")
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=10)
        if response.status_code == 200:
            # Just show first few lines
            lines = response.text.split('\n')[:10]
            print("✓ Metrics endpoint available")
            print("  Sample metrics:")
            for line in lines:
                if line and not line.startswith('#'):
                    print(f"    {line[:60]}...")
                    break
        return True
    except Exception as e:
        print(f"  Metrics not available: {e}")
        return False

def main():
    """Run the full API flow test"""
    print("\n" + "🚀 " * 20)
    print("       FULL API FLOW TEST")
    print("🚀 " * 20)
    print(f"\nBase URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    # Step 1: Health check
    if not test_health():
        print("\n❌ Server not available. Please start the services first:")
        print("   1. Start Redis")
        print("   2. Start Celery: python -m celery -A app.celery_app worker --loglevel=info --pool=solo")
        print("   3. Start FastAPI: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Step 2: Submit generation request
    prompt = "Write a short poem about artificial intelligence and the future of technology."
    task_id = test_generate(prompt)
    
    if not task_id:
        print("\n❌ Failed to submit request")
        sys.exit(1)
    
    # Step 3: Check status
    test_status(task_id)
    
    # Step 4: Wait for and get result
    result = test_result(task_id)
    
    if result:
        display_result(result)
    
    # Bonus: Check metrics
    test_metrics()
    
    print_separator("TEST COMPLETE")
    print("✓ All API endpoints tested successfully!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
