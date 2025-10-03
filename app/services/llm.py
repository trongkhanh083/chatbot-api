from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_mistralai import ChatMistralAI
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL, MISTRAL_API_KEY
import logging

logger = logging.getLogger(__name__)

# Initialize LLM
# llm = ChatOllama(
#     model=LLM_MODEL,
#     base_url=OLLAMA_BASE_URL, 
#     temperature=0.3,
#     num_ctx=4096,
#     num_thread=8,
#     num_gpu=1,
#     top_k=40,
#     top_p=0.9,
#     repeat_penalty=1.1,
#     timeout=60
# )

llm = ChatMistralAI(
    model=LLM_MODEL,
    mistral_api_key=MISTRAL_API_KEY,
    temperature=0.3,
    top_p=0.9
)

# Initialize embeddings
# embeddings = OllamaEmbeddings(
#     model=EMBEDDING_MODEL, 
#     base_url=OLLAMA_BASE_URL
# )

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)