from langchain_core.tools import tool
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.services.qdrant_store import get_qdrant_vector_store
from app.services.cache import cached_similarity_search
import time
import re

# Initialize Qdrant vector store
try:
    qdrant_store = get_qdrant_vector_store()
    print("✅ Vector store initialized in retrieval")
except Exception as e:
    print(f"❌ Failed to initialize Qdrant vector store: {e}")
    qdrant_store = None

@tool
def retrieve(query: str):
    """Retrieve information related to a query with caching using Qdrant."""
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
            department = doc.metadata.get('department', 'N/A')
            doc_type = doc.metadata.get('doc_type', 'N/A')
            
            results.append(
                f"📄 Title: {title}\n"
                f"🏢 Department: {department} | Type: {doc_type}\n"
                f"🔗 Source: {source}\n"
                f"📝 Content: {doc.page_content[:500]}..."
            )
        
        end_time = time.time()
        print(f"🔍 Basic retrieval took {end_time - start_time:.2f} seconds")
        
        return "\n\n".join(results)
        
    except Exception as e:
        print(f"❌ Retrieval error: {e}")
        # Fallback to direct search without cache
        try:
            if qdrant_store:
                retrieved_docs = qdrant_store.similarity_search(query, k=2)
                if retrieved_docs:
                    result = ""
                    for doc in retrieved_docs:
                        title = doc.metadata.get('title', 'No title')
                        result += f"📄 {title}:\n{doc.page_content[:500]}...\n\n"
                    return result
            return "Error during search. Please try again."
        except Exception as fallback_error:
            print(f"❌ Fallback search failed: {fallback_error}")
            return "Search service unavailable. Please try again later."

def enhanced_retrieval(query: str, filters: dict = None, k: int = 5, return_formatted: bool = False):
    """Enhanced retrieval with metadata filtering for Qdrant"""
    start_time = time.time()

    try:
        if not qdrant_store:
            return [] if not return_formatted else "Vector store not available"
        
        # Build search parameters
        search_kwargs = {"k": k}
        
        # Add metadata filtering if provided
        if filters:
            conditions = []
            
            for key, value in filters.items():
                if value:  # Only add non-empty filters
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            
            if conditions:
                search_kwargs["filter"] = Filter(must=conditions)
        
        # Perform search
        retrieved_docs = qdrant_store.similarity_search(query, **search_kwargs)
        
        # Return formatted string if requested
        if return_formatted:
            if not retrieved_docs:
                return "No relevant information found."

            # Format results efficiently
            results = []
            for doc in retrieved_docs:
                source = doc.metadata.get('source', 'Unknown')
                title = doc.metadata.get('title', 'No title')
                department = doc.metadata.get('department', 'N/A')
                doc_type = doc.metadata.get('doc_type', 'N/A')
                
                results.append(
                    f"📄 Title: {title}\n"
                    f"🏢 Department: {department} | Type: {doc_type}\n"
                    f"🔗 Source: {source}\n"
                    f"📝 Content: {doc.page_content}"
                )
        
            end_time = time.time()
            print(f"🔍 Enhanced retrieval took {end_time - start_time:.2f} seconds")
        
            return "\n\n".join(results)
        else:
            # Return raw document objects for API endpoints
            end_time = time.time()
            print(f"🔍 Qdrant retrieval took {end_time - start_time:.2f} seconds")
            return retrieved_docs
        
    except Exception as e:
        print(f"❌ Enhanced retrieval error: {e}")
        return []

@tool
def retrieve_with_filters(query: str, department: str = None, doc_type: str = None, year: int = None):
    """Retrieve information with metadata filtering."""
    start_time = time.time()
    
    try:
        # Build filters
        filters = {}
        if department and department.lower() != "any":
            filters["department"] = department
        if doc_type and doc_type.lower() != "any":
            filters["doc_type"] = doc_type
        if year:
            filters["year"] = year
        
        # Perform filtered search
        retrieved_docs = enhanced_retrieval(query, filters=filters, k=3)
        
        if not retrieved_docs:
            return "No relevant information found with the specified filters."
        
        # Format results
        results = []
        for doc in retrieved_docs:
            title = doc.metadata.get('title', 'No title')
            dept = doc.metadata.get('department', 'N/A')
            doc_type = doc.metadata.get('doc_type', 'N/A')
            year = doc.metadata.get('year', 'N/A')
            security = doc.metadata.get('security_level', 'N/A')
            
            results.append(
                f"📄 {title}\n"
                f"🏢 {dept} | 📁 {doc_type} | 📅 {year} | 🔒 {security}\n"
                f"📝 {doc.page_content[:500]}..."
            )
        
        end_time = time.time()
        print(f"🔍 Filtered retrieval took {end_time - start_time:.2f} seconds")
        
        return "\n\n".join(results)
        
    except Exception as e:
        print(f"❌ Filtered retrieval error: {e}")
        return "Error during filtered search. Please try again."

def extract_filters_from_query(query: str):
    """Extract potential filters from user query with improved matching"""
    filters = {}
    query_lower = query.lower().strip()
    
    # Department filters with better matching
    departments = {
        "ai research": "AI Research",
        "ml engineering": "ML Engineering", 
        "data science": "Data Science",
        "product": "Product",
        "engineering": "Engineering",
        "r&d": "R&D",
        "analytics": "Analytics",
        "platform": "Platform"
    }
    
    for dept_key, dept_value in departments.items():
        if dept_key in query_lower:
            filters["department"] = dept_value
            break
        # Also check for partial matches
        elif any(word in query_lower.split() for word in dept_key.split()):
            filters["department"] = dept_value
            break
    
    # Document type filters with better matching
    doc_types = {
        "research paper": "Research Paper",
        "technical guide": "Technical Guide",
        "api documentation": "API Documentation",
        "best practices": "Best Practices",
        "implementation guide": "Implementation Guide",
        "technical report": "Technical Report",
        "system design": "System Design",
        "tutorial": "Tutorial",
        "paper": "Research Paper",
        "guide": "Technical Guide",
        "documentation": "API Documentation",
        "report": "Technical Report",
        "design": "System Design"
    }
    
    for doc_key, doc_value in doc_types.items():
        if doc_key in query_lower:
            filters["doc_type"] = doc_value
            break
        # Check for individual words
        elif any(word in query_lower.split() for word in doc_key.split()):
            filters["doc_type"] = doc_value
            break
    
    # Year filters (looking for years 2018-2025)
    year_pattern = r'\b(20[1-2][0-9])\b'
    year_matches = re.findall(year_pattern, query)
    if year_matches:
        filters["year"] = int(year_matches[0])
    
    # Additional context-based filters
    words = query_lower.split()
    
    # Check for time-related words
    time_words = ["recent", "latest", "new", "current", "old", "previous", "past"]
    for word in time_words:
        if word in query_lower:
            if word in ["recent", "latest", "new", "current"]:
                filters["year"] = 2024  # Default to current year
            break
    
    # Check for security level hints
    security_words = ["confidential", "secret", "internal", "public", "restricted"]
    for word in security_words:
        if word in query_lower:
            filters["security_level"] = word.title()
            break
    
    print(f"🔍 Extracted filters from query '{query}': {filters}")

    return filters

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
        "thank you", "bye", "goodbye", "ok", "okay"
    ]
    
    # If it's a simple greeting or conversation, respond directly
    if any(query.startswith(simple) for simple in simple_queries):
        return False
    
    # If it's a very short query that's not a question
    if len(query.split()) < 3 and "?" not in query:
        return False
        
    return True
