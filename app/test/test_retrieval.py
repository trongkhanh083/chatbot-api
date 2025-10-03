from app.services.qdrant_store import qdrant_vector_store as qdrant_store

def test_qdrant_retrieval():
    """Test Qdrant retrieval functionality"""
    if not qdrant_store:
        print("❌ Qdrant store not available")
        return
    
    test_queries = [
        "machine learning",
        "neural networks",
        "AI research papers",
        "technical guides for data science"
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing: '{query}'")
        try:
            results = qdrant_store.similarity_search(query, k=2)
            print(f"✅ Found {len(results)} results")
            for i, doc in enumerate(results):
                print(f"  {i+1}. {doc.metadata.get('title', 'No title')}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_qdrant_retrieval()