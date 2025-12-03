#!/usr/bin/env python
"""
Quick start script to test the LLM Inference System.
Submits a test request and displays the result.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client_example import LLMClient


def main():
    print("="*80)
    print("LLM INFERENCE SYSTEM - QUICK TEST")
    print("="*80)
    print()
    
    # Configuration
    API_URL = input("API URL [http://localhost:8000]: ").strip() or "http://localhost:8000"
    API_KEY = input("API Key [dev-key-12345]: ").strip() or "dev-key-12345"
    
    print()
    
    # Initialize client
    client = LLMClient(API_URL, API_KEY)
    
    # Health check
    print("🏥 Checking system health...")
    try:
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Redis Connected: {'✓' if health['redis_connected'] else '✗'}")
        print(f"   Model Loaded: {'✓' if health['model_loaded'] else '✗'}")
        
        if not health['redis_connected']:
            print("\n⚠️  WARNING: Redis is not connected!")
            print("   Please start Redis before continuing.")
            return
        
        if not health['model_loaded']:
            print("\n⚠️  WARNING: Model is not loaded in worker!")
            print("   Please start the Celery worker before continuing.")
            return
        
        print("   ✓ System is healthy!")
    except Exception as e:
        print(f"\n✗ Health check failed: {str(e)}")
        print("\nPlease ensure:")
        print("  1. FastAPI server is running (uvicorn app.main:app)")
        print("  2. Redis is running")
        print("  3. Celery worker is running")
        return
    
    print()
    print("="*80)
    
    # Get prompt from user
    print("\nEnter your prompt (or press Enter for default):")
    prompt = input("> ").strip()
    
    if not prompt:
        prompt = "Write a haiku about artificial intelligence."
        print(f"Using default prompt: {prompt}")
    
    print()
    
    # Generate
    try:
        result = client.generate(
            prompt=prompt,
            max_tokens=256,
            temperature=0.7,
            wait=True,
            verbose=True
        )
        
        if result.get("status") == "completed":
            print("\n" + "="*80)
            print("📄 GENERATED TEXT:")
            print("="*80)
            print(result["result"])
            print("\n" + "="*80)
            print("📊 PERFORMANCE METRICS:")
            print("="*80)
            metrics = result.get("metrics", {})
            print(f"  Queue Wait Time:    {metrics.get('queue_wait_time', 0):.2f}s")
            print(f"  Processing Time:    {metrics.get('processing_time', 0):.2f}s")
            print(f"  Total Time:         {metrics.get('total_time', 0):.2f}s")
            print(f"  Prompt Tokens:      {metrics.get('prompt_tokens', 0)}")
            print(f"  Completion Tokens:  {metrics.get('completion_tokens', 0)}")
            print(f"  Tokens/Second:      {metrics.get('tokens_per_second', 0):.2f}")
            print("="*80)
            print("\n✓ Test completed successfully!")
        else:
            print(f"\n✗ Generation failed: {result.get('error_message')}")
            print(f"   Error type: {result.get('error_type')}")
            print("\nCheck logs/errors.log for detailed traceback.")
    
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nPlease check:")
        print("  1. API URL is correct")
        print("  2. API key is valid")
        print("  3. System logs for errors")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)
