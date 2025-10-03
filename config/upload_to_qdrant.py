import json
import os
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from app.services.llm import embeddings
from config.settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import logging

logger = logging.getLogger(__name__)

def get_qdrant_client():
    """Initialize Qdrant client"""
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
    return client

def load_documents_from_json(json_file_path):
    """Load documents from the generated JSON file"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    for doc_data in data:
        # Create LangChain Document objects
        document = Document(
            page_content=doc_data["content"],
            metadata=doc_data["metadata"]
        )
        documents.append(document)
    
    print(f"📁 Loaded {len(documents)} documents from {json_file_path}")
    return documents

def create_qdrant_collection(client, collection_name, vector_size=384):
    """Create Qdrant collection if it doesn't exist"""
    try:
        # Get collections
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if collection_name in collection_names:
            print(f"✅ Collection '{collection_name}' already exists")
            return False
        else:
            # Create new collection
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"✅ Created new collection: '{collection_name}'")
            return True
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        raise

def upload_documents_to_qdrant(documents, batch_size=50):
    """Upload documents to Qdrant vector store"""
    client = get_qdrant_client()
    
    # Create collection (if needed)
    create_qdrant_collection(client, QDRANT_COLLECTION_NAME)
    
    # Initialize Qdrant vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION_NAME,
        embedding=embeddings,
    )
    
    print(f"🔄 Uploading {len(documents)} documents to Qdrant...")
    
    # Upload in batches to avoid memory issues
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        vector_store.add_documents(batch)
        print(f"✅ Uploaded batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} - {len(batch)} documents")
    
    print(f"🎉 Successfully uploaded {len(documents)} documents to Qdrant!")
    return vector_store

def find_latest_json_file(data_folder="data"):
    """Find the most recent JSON file in data folder"""
    if not os.path.exists(data_folder):
        raise FileNotFoundError(f"Data folder '{data_folder}' not found")
    
    json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in '{data_folder}'")
    
    # Get the most recent file
    latest_file = max(json_files, key=lambda f: os.path.getctime(os.path.join(data_folder, f)))
    return os.path.join(data_folder, latest_file)

def main():
    """Main function to upload documents to Qdrant"""
    try:
        # Find the latest generated JSON file
        json_file_path = find_latest_json_file()
        print(f"📂 Using file: {json_file_path}")
        
        # Load documents
        documents = load_documents_from_json(json_file_path)
        
        # Upload to Qdrant
        vector_store = upload_documents_to_qdrant(documents)
        
        # Test retrieval
        print("\n🧪 Testing retrieval...")
        test_results = vector_store.similarity_search("machine learning", k=2)
        print(f"✅ Test search returned {len(test_results)} results")
        
        for i, doc in enumerate(test_results):
            print(f"\nResult {i+1}:")
            print(f"Title: {doc.metadata.get('title', 'N/A')}")
            print(f"Content: {doc.page_content[:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()