from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback
from langchain_core.messages import HumanMessage
from typing import List, Optional
from app.core.agent import run_agent, safe_convert_to_string
from app.tools.qdrant_retrieval import retrieve, retrieve_with_filters, enhanced_retrieval, extract_filters_from_query
from app.core.memory import get_conversation_history, clear_conversation_history
from app.core.agent import run_agent

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

class ChatResponse(BaseModel):
    response: str

class RetrievalRequest(BaseModel):
    query: str
    department: Optional[str] = None
    doc_type: Optional[str] = None
    year: Optional[int] = None

class FilteredRetrievalRequest(BaseModel):
    query: str
    department: Optional[str] = None
    doc_type: Optional[str] = None
    year: Optional[int] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        human_message = HumanMessage(content=request.message)
        ai_message = run_agent(human_message, thread_id=request.thread_id)

        if ai_message is None:
            raise HTTPException(status_code=500, detail="No response from agent")
        
        # Debug the content before processing
        print(f"Raw AI message content: {ai_message.content}")
        print(f"Raw AI message content type: {type(ai_message.content)}")
        
        # Double-check content type
        if not isinstance(ai_message.content, str):
            print(f"Warning: Content is not string, type: {type(ai_message.content)}")

        response_content = safe_convert_to_string(ai_message.content)

        return ChatResponse(response=response_content)
    
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/retrieval")
async def test_retrieval(request: RetrievalRequest):
    """Test if Qdrant retrieval is working properly."""
    try:
        # Use the retrieve tool from your qdrant_retrieval.py
        results = retrieve.invoke(request.query)
        
        return {
            "success": True,
            "query": request.query,
            "results": results,
            "retrieval_type": "qdrant_basic"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": request.query,
            "retrieval_type": "qdrant_basic"
        }

@router.post("/retrieval/filter")
async def test_filtered_retrieval(request: FilteredRetrievalRequest):
    """Test Qdrant retrieval with metadata filtering."""
    try:
        # Use the retrieve_with_filters tool
        results = retrieve_with_filters.invoke({
            "query": request.query,
            "department": request.department,
            "doc_type": request.doc_type,
            "year": request.year
        })
        
        return {
            "success": True,
            "query": request.query,
            "filters": {
                "department": request.department,
                "doc_type": request.doc_type,
                "year": request.year
            },
            "results": results,
            "retrieval_type": "qdrant_filtered"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": request.query,
            "filters": {
                "department": request.department,
                "doc_type": request.doc_type,
                "year": request.year
            },
            "retrieval_type": "qdrant_filtered"
        }

@router.post("/retrieval/enhance")
async def test_enhanced_retrieval(request: RetrievalRequest):
    """Test enhanced Qdrant retrieval with automatic filter extraction."""
    try:
        # Extract filters from query automatically
        filters = extract_filters_from_query(request.query)
        
        # Use enhanced retrieval
        results = enhanced_retrieval(request.query, filters=filters, k=5, return_formatted=True)
        
        return {
            "success": True,
            "query": request.query,
            "extracted_filters": filters,
            "results_count": len(results),
            "results": results,
            "retrieval_type": "qdrant_enhanced"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": request.query,
            "retrieval_type": "qdrant_enhanced"
        }

@router.get("/retrieval/analyze")
async def analyze_query_filters(query: str):
    """Analyze a query and extract potential filters with detailed analysis."""
    try:
        filters = extract_filters_from_query(query)
        
        # Detailed analysis of why filters were/were not found
        analysis = {
            "query_analyzed": query,
            "query_lowercase": query.lower(),
            "words_in_query": query.lower().split(),
            "filter_matches": {}
        }
        
        # Check for department matches
        departments = ["ai research", "ml engineering", "data science", "product", "engineering", "r&d", "analytics", "platform"]
        analysis["filter_matches"]["departments"] = []
        for dept in departments:
            if dept in query.lower():
                analysis["filter_matches"]["departments"].append({
                    "department": dept,
                    "found": True,
                    "match_type": "exact"
                })
            elif any(word in query.lower().split() for word in dept.split()):
                analysis["filter_matches"]["departments"].append({
                    "department": dept,
                    "found": True,
                    "match_type": "partial"
                })
            else:
                analysis["filter_matches"]["departments"].append({
                    "department": dept,
                    "found": False,
                    "match_type": "none"
                })
        
        # Check for document type matches
        doc_types = ["research paper", "technical guide", "api documentation", "best practices", 
                    "implementation guide", "technical report", "system design", "tutorial"]
        analysis["filter_matches"]["document_types"] = []
        for doc_type in doc_types:
            if doc_type in query.lower():
                analysis["filter_matches"]["document_types"].append({
                    "doc_type": doc_type,
                    "found": True,
                    "match_type": "exact"
                })
            elif any(word in query.lower().split() for word in doc_type.split()):
                analysis["filter_matches"]["document_types"].append({
                    "doc_type": doc_type,
                    "found": True,
                    "match_type": "partial"
                })
            else:
                analysis["filter_matches"]["document_types"].append({
                    "doc_type": doc_type,
                    "found": False,
                    "match_type": "none"
                })
        
        # Check for year matches
        import re
        year_pattern = r'\b(20[1-2][0-9])\b'
        year_matches = re.findall(year_pattern, query)
        analysis["filter_matches"]["years"] = {
            "found_years": year_matches,
            "pattern_used": year_pattern
        }
        
        return {
            "success": True,
            "query": query,
            "extracted_filters": filters,
            "analysis": analysis,
            "suggested_filters": {
                "available_departments": ["AI Research", "ML Engineering", "Data Science", "Product", "Engineering", "R&D", "Analytics", "Platform"],
                "available_doc_types": ["Research Paper", "Technical Guide", "API Documentation", "Best Practices", "Implementation Guide", "Technical Report", "System Design", "Tutorial"],
                "available_years": list(range(2018, 2025)),
                "example_queries_with_filters": [
                    "AI research papers from 2023",
                    "ML engineering technical guides",
                    "Data science best practices 2024",
                    "System design documentation",
                    "R&D technical reports from 2022"
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
    
@router.get("/conversation/{thread_id}", response_model=List[dict])
async def get_conversation(thread_id: str):
    """Get conversation history for a thread."""
    messages = get_conversation_history(thread_id)
    return [{"type": msg.type, "content": msg.content} for msg in messages]

@router.delete("/conversation/{thread_id}")
async def clear_conversation(thread_id: str):
    """Clear conversation history for a thread."""
    success = clear_conversation_history(thread_id)
    if success:
        return {"message": "Conversation cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear conversation")
    