"""
LLM Client Usage Examples
=========================
Copy this file to your other projects and modify as needed.
"""

# ============================================================================
# SETUP: Copy llm_client.py to your project, or add this to your path
# ============================================================================

from llm_client import LLM, chat, generate, stream_chat, create_coder, create_assistant


# ============================================================================
# EXAMPLE 1: Quick One-Liners (Simplest Usage)
# ============================================================================

def example_quick_usage():
    """Simplest way to use - just like OpenAI's quick functions."""
    
    # Basic chat - returns string directly
    response = chat("What is Python?")
    print(response)
    
    # With system prompt
    response = chat(
        "Explain recursion",
        system="You are a patient coding tutor for beginners"
    )
    print(response)
    
    # Raw text generation (no chat format)
    response = generate("Complete this code:\ndef fibonacci(n):")
    print(response)


# ============================================================================
# EXAMPLE 2: Full Control with LLM Class
# ============================================================================

def example_full_control():
    """Full control over all parameters."""
    
    # Create client with custom settings
    llm = LLM(
        model="qwen2.5-coder:14b",      # Your model
        base_url="http://localhost:11434",  # Ollama server
        system_prompt="You are a senior Python developer",
        temperature=0.3,                 # Lower = more deterministic
        max_tokens=4096,                 # Max response length
        top_p=0.9,                       # Nucleus sampling
        timeout=120,                     # Request timeout
    )
    
    # Chat with the configured client
    response = llm.chat("How do I implement a binary search tree?")
    print(response.content)
    print(f"Tokens used: {response.usage.total_tokens}")
    
    # Override settings per-request
    response = llm.chat(
        "Write a haiku about coding",
        temperature=0.9,  # Higher for creativity
        max_tokens=100,
    )
    print(response.content)


# ============================================================================
# EXAMPLE 3: Streaming Responses
# ============================================================================

def example_streaming():
    """Stream responses token by token - great for UIs."""
    
    llm = LLM(model="qwen2.5-coder:14b")
    
    print("Streaming response: ", end="")
    for chunk in llm.stream("Write a short poem about debugging"):
        print(chunk, end="", flush=True)
    print()  # Newline at end
    
    # Or use the quick function
    for chunk in stream_chat("Tell me a joke", system="You are a comedian"):
        print(chunk, end="", flush=True)
    print()


# ============================================================================
# EXAMPLE 4: Conversation with Context
# ============================================================================

def example_conversation():
    """Multi-turn conversation with context."""
    
    llm = LLM(
        model="qwen2.5-coder:14b",
        system_prompt="You are a helpful coding assistant"
    )
    
    # Build conversation history
    history = []
    
    # Turn 1
    user_msg = "What is a decorator in Python?"
    response = llm.chat(user_msg, context=history)
    print(f"User: {user_msg}")
    print(f"Assistant: {response.content}\n")
    
    # Add to history
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": response.content})
    
    # Turn 2 - follows up on previous context
    user_msg = "Can you show me an example?"
    response = llm.chat(user_msg, context=history)
    print(f"User: {user_msg}")
    print(f"Assistant: {response.content}\n")


# ============================================================================
# EXAMPLE 5: Pre-configured Specialized Clients
# ============================================================================

def example_specialized_clients():
    """Use pre-configured clients for specific tasks."""
    
    # Coding assistant (low temperature, code-focused prompt)
    coder = create_coder()
    response = coder.chat("Write a function to validate email addresses")
    print("Coder:", response.content)
    
    # General assistant
    assistant = create_assistant()
    response = assistant.chat("What's the weather like today?")
    print("Assistant:", response.content)


# ============================================================================
# EXAMPLE 6: Error Handling
# ============================================================================

def example_error_handling():
    """Proper error handling."""
    
    from llm_client import LLMError, ConnectionError, ModelNotFoundError, TimeoutError
    
    try:
        llm = LLM(model="nonexistent-model")
        response = llm.chat("Hello")
    except ConnectionError:
        print("❌ Ollama is not running! Start with: ollama serve")
    except ModelNotFoundError as e:
        print(f"❌ Model not found: {e}")
    except TimeoutError:
        print("❌ Request timed out")
    except LLMError as e:
        print(f"❌ LLM Error: {e}")


# ============================================================================
# EXAMPLE 7: Check Available Models
# ============================================================================

def example_list_models():
    """List and check available models."""
    
    llm = LLM()
    
    # Check if server is available
    if llm.is_available():
        print("✅ Ollama is running")
        print(f"📦 Available models: {llm.list_models()}")
    else:
        print("❌ Ollama is not running")


# ============================================================================
# EXAMPLE 8: Custom System Prompts for Different Tasks
# ============================================================================

def example_custom_prompts():
    """Different system prompts for different tasks."""
    
    # Code reviewer
    reviewer = LLM(
        system_prompt="""You are a senior code reviewer. 
        Review code for:
        - Bugs and potential issues
        - Performance problems
        - Security vulnerabilities
        - Code style and best practices
        Be constructive and specific.""",
        temperature=0.3,
    )
    
    code = '''
    def get_user(id):
        query = f"SELECT * FROM users WHERE id = {id}"
        return db.execute(query)
    '''
    
    response = reviewer.chat(f"Review this code:\n```python{code}```")
    print("Code Review:", response.content)
    
    # SQL Expert
    sql_expert = LLM(
        system_prompt="You are a SQL expert. Write efficient, optimized queries.",
        temperature=0.2,
    )
    
    response = sql_expert.chat("Write a query to find duplicate emails in a users table")
    print("SQL:", response.content)


# ============================================================================
# EXAMPLE 9: Integration Pattern for Your Projects
# ============================================================================

# This is how you'd typically integrate in a real project:

class MyProjectAI:
    """
    Example: Wrap the LLM client for your specific project.
    Copy and customize this pattern.
    """
    
    def __init__(self):
        self.llm = LLM(
            model="qwen2.5-coder:14b",
            system_prompt="You are an AI assistant for MyProject application.",
            temperature=0.7,
        )
    
    def analyze_data(self, data: str) -> str:
        """Analyze data using AI."""
        return self.llm.chat(
            f"Analyze this data and provide insights:\n{data}",
            temperature=0.4,  # Lower for analysis
        ).content
    
    def generate_report(self, topic: str) -> str:
        """Generate a report on a topic."""
        return self.llm.chat(
            f"Generate a detailed report on: {topic}",
            max_tokens=4096,
        ).content
    
    def answer_question(self, question: str) -> str:
        """Answer a user question."""
        return self.llm.chat(question).content


# ============================================================================
# RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("LLM Client Examples")
    print("=" * 60)
    
    # Check connection first
    from llm_client import LLM
    llm = LLM()
    
    if not llm.is_available():
        print("\n❌ Ollama is not running!")
        print("   Start it with: ollama serve")
        exit(1)
    
    print(f"\n✅ Connected to Ollama")
    print(f"📦 Models: {llm.list_models()}")
    
    # Run a simple test
    print("\n" + "-" * 60)
    print("Quick test:")
    response = chat("Say 'Hello!' and nothing else")
    print(f"Response: {response}")
    
    print("\n" + "=" * 60)
    print("See the code above for more examples!")
    print("=" * 60)
