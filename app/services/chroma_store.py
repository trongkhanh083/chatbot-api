import bs4
from langchain_chroma import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.llm import embeddings
from config.settings import BLOG_URL

COLLECTION_NAME = "chatbot_collection"
PERSIST_DIR = "./chroma_db"

# Initilize placeholder
vector_store = None

def get_vector_store():
    """Load vector store from disk."""
    return Chroma(
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
    )

def load_and_index_documents():
    """Fetch, split, and persist documents into Chroma vector store."""
    global vector_store

    loader = WebBaseLoader(
        web_paths=(BLOG_URL,),
        bs_kwargs=dict(
            parse_only=bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        ),
    )
    docs = loader.load()
    print(f"✅ Loaded {len(docs)} documents from the web")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    all_splits = text_splitter.split_documents(docs)
    print(f"✅ Split into {len(all_splits)} chunks")

    # Create and persist the vector store
    vector_store = Chroma.from_documents(
        documents=all_splits,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
    )
    print("✅ Indexed and persisted Chroma vector store")

    return vector_store

# Try to load existing vector store on import
try:
    vector_store = get_vector_store()
    print("✅ Loaded existing Chroma vector store")
except Exception as e:
    print("⚠️ Failed to load existing store. Call load_and_index_documents() manually.")
    vector_store = None
