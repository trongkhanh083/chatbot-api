from langchain_core.tools import tool
from app.services.chroma_store import chroma_store
from app.services.cache import cached_similarity_search
import time

@tool
def retrieve(query: str):
    """Retrieve information related to a query with caching."""
    start_time = time.time()
    
    try:
        # Use cached search results
        retrieved_docs = cached_similarity_search(query, k=3)
        
        if not retrieved_docs:
            return "No relevant information found."
        
        # Format results efficiently
        results = []
        for doc in retrieved_docs:
            source = doc.metadata.get('source', 'Unknown')
            title = doc.metadata.get('title', 'No title')
            results.append(f"Source: {source} | {title}\nContent: {doc.page_content[:500]}...")
        
        end_time = time.time()
        print(f"Retrieval took {end_time - start_time:.2f} seconds")
        
        return "\n\n".join(results)
        
    except Exception as e:
        print(f"Retrieval error: {e}")
        # Fallback to direct search without cache
        try:
            retrieved_docs = chroma_store.similarity_search(query, k=2)
            if retrieved_docs:
                return f"Content: {retrieved_docs[0].page_content[:300]}..."
            return "Error during search. Please try again."
        except:
            return "Search service unavailable."

def needs_retrieval(state):
    """Determine if the query needs retrieval or can be answered directly."""
    messages = state["messages"]
    if not messages:
        return False
    
    last_message = messages[-1]
    query = last_message.content.lower().strip()
    
    # Queries that don't need retrieval
    simple_queries = [
        "hello", "hi", "hey", "greetings", 
        "how are you", "what's up", "good morning",
        "good afternoon", "good evening", "thanks",
        "thank you", "bye", "goodbye"
    ]
    
    # If it's a simple greeting or conversation, respond directly
    if any(query.startswith(simple) for simple in simple_queries):
        return False
    
    # If it's a very short query that's not a question
    if len(query.split()) < 3 and "?" not in query:
        return False
        
    return True