import os
from dotenv import load_dotenv

load_dotenv()

# Configuration settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")