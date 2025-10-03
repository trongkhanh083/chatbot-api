from app.services.qdrant_store import get_qdrant_vector_store

def verify_upload():
    vector_store = get_qdrant_vector_store()
    
    # Test search
    results = vector_store.similarity_search("neural networks", k=3)
    
    print(f"✅ Found {len(results)} documents")
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Department: {doc.metadata.get('department', 'N/A')}")
        print(f"Content preview: {doc.page_content[:150]}...")
    
    return len(results) > 0

if __name__ == "__main__":
    verify_upload()