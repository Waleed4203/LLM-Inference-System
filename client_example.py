"""
Simple Python client for testing the LLM Inference System.
"""
import requests
import time
import sys
from typing import Optional


class LLMClient:
    """Client for interacting with LLM Inference System API."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize client.
        
        Args:
            base_url: Base URL of the API (e.g., http://localhost:8000)
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> dict:
        """Check API health status."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def submit_request(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        user_id: Optional[str] = None
    ) -> str:
        """
        Submit a generation request.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            user_id: Optional user identifier
            
        Returns:
            task_id for tracking the request
        """
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        if user_id:
            payload["user_id"] = user_id
        
        response = requests.post(
            f"{self.base_url}/generate",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return data["task_id"]
    
    def get_status(self, task_id: str) -> dict:
        """Get task status."""
        response = requests.get(
            f"{self.base_url}/status/{task_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_result(self, task_id: str) -> dict:
        """Get task result."""
        response = requests.get(
            f"{self.base_url}/result/{task_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_result(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        verbose: bool = True
    ) -> dict:
        """
        Wait for task to complete and return result.
        
        Args:
            task_id: Task identifier
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            verbose: Print status updates
            
        Returns:
            Result dictionary
            
        Raises:
            TimeoutError: If task doesn't complete within timeout
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
            
            result = self.get_result(task_id)
            status = result.get("status")
            
            if status == "completed":
                if verbose:
                    print(f"\n✓ Task completed!")
                return result
            elif status == "error":
                if verbose:
                    print(f"\n✗ Task failed: {result.get('error_message')}")
                return result
            else:
                if verbose:
                    print(f"⏳ Status: {status}... waiting ({elapsed:.1f}s elapsed)", end='\r')
                time.sleep(poll_interval)
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        user_id: Optional[str] = None,
        wait: bool = True,
        verbose: bool = True
    ) -> dict:
        """
        Convenience method to submit request and optionally wait for result.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            user_id: Optional user identifier
            wait: Whether to wait for result
            verbose: Print status updates
            
        Returns:
            Result dictionary if wait=True, else dict with task_id
        """
        if verbose:
            print(f"📝 Submitting request...")
            print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        
        task_id = self.submit_request(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            user_id=user_id
        )
        
        if verbose:
            print(f"✓ Task queued: {task_id}")
        
        if wait:
            return self.wait_for_result(task_id, verbose=verbose)
        else:
            return {"task_id": task_id, "status": "queued"}


def main():
    """Example usage."""
    # Configuration
    API_URL = "http://localhost:8000"
    API_KEY = "dev-key-12345"  # Change to your API key
    
    # Initialize client
    client = LLMClient(API_URL, API_KEY)
    
    # Check health
    print("🏥 Checking API health...")
    health = client.health_check()
    print(f"Status: {health['status']}")
    print(f"Redis: {'✓' if health['redis_connected'] else '✗'}")
    print(f"Model: {'✓' if health['model_loaded'] else '✗'}")
    print()
    
    # Generate text
    prompt = "Explain quantum computing in simple terms."
    
    print("="*80)
    result = client.generate(
        prompt=prompt,
        max_tokens=256,
        temperature=0.7,
        wait=True,
        verbose=True
    )
    
    if result.get("status") == "completed":
        print("\n" + "="*80)
        print("📄 RESULT:")
        print("="*80)
        print(result["result"])
        print("\n" + "="*80)
        print("📊 METRICS:")
        print("="*80)
        metrics = result.get("metrics", {})
        print(f"Queue Wait Time:    {metrics.get('queue_wait_time', 0):.2f}s")
        print(f"Processing Time:    {metrics.get('processing_time', 0):.2f}s")
        print(f"Total Time:         {metrics.get('total_time', 0):.2f}s")
        print(f"Prompt Tokens:      {metrics.get('prompt_tokens', 0)}")
        print(f"Completion Tokens:  {metrics.get('completion_tokens', 0)}")
        print(f"Tokens/Second:      {metrics.get('tokens_per_second', 0):.2f}")
        print("="*80)
    else:
        print(f"\n✗ Error: {result.get('error_message')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
