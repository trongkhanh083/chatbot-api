from langchain_core.messages import HumanMessage
from app.core.agent import run_agent

def test_qdrant_agent():
    """Test function to verify Qdrant agent is working."""
    test_queries = [
        "What is machine learning?",
        "Show me research papers about neural networks",
        "Find technical guides from the AI Research department",
        "Explain reinforcement learning"
    ]
    
    print("🧪 Testing Qdrant Agent...")
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        try:
            response = run_agent(HumanMessage(content=query))
            if response and hasattr(response, 'content'):
                print(f"✅ Response: {response.content[:200]}...")
            else:
                print("❌ No response generated")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_qdrant_agent()