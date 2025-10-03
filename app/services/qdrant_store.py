from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from app.services.llm import embeddings
from config.settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME
import logging

logger = logging.getLogger(__name__)

def get_qdrant_client():
    """Initialize Qdrant client"""
    try:
        if QDRANT_API_KEY:
            # For Qdrant Cloud
            client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY
            )
        else:
            # For local Qdrant
            client = QdrantClient(
                url=QDRANT_URL
            )
        
        # Test connection
        client.get_collections()
        print("✅ Qdrant client connected")
        return client
        
    except Exception as e:
        print(f"❌ Qdrant client connection failed: {e}")
        raise

def get_qdrant_vector_store():
    """Get Qdrant vector store for queries"""
    try:
        client = get_qdrant_client()
        
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION_NAME,
            embedding=embeddings,
        )
        
        # Test the vector store
        vector_store.similarity_search("test", k=1)
        print("✅ Qdrant vector store initialized")
        
        return vector_store
        
    except Exception as e:
        print(f"❌ Qdrant vector store initialization failed: {e}")
        return None

# Global instance
qdrant_vector_store = get_qdrant_vector_store()