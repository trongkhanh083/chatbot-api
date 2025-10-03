from app.services.llm import llm, embeddings

def test_models():
    """Test that both models are working"""
    try:
        # Test LLM
        test_response = llm.invoke("Hello, are you working?")
        print(f"✅ LLM test: {test_response.content[:100]}...")
        
        # Test embeddings
        test_embedding = embeddings.embed_query("test sentence")
        print(f"✅ Embeddings test: Vector size {len(test_embedding)}")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False
    
if __name__ == "__main__":
    test_models()