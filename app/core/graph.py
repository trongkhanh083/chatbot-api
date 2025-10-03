from langchain_core.messages import SystemMessage
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

from app.services.llm import llm
from app.tools.qdrant_retrieval import retrieve, retrieve_with_filters, needs_retrieval, extract_filters_from_query
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Add timing decorator
def time_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def safe_join_content(content):
    """Safely join content whether it's a string, list, or other type."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Handle list of strings or other objects
        return ' '.join(str(item) for item in content)
    return str(content)

# Generate an AIMessage that may include a tool-call to be sent.
@time_execution
def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond using Qdrant."""
    if needs_retrieval(state):
        last_message = state["messages"][-1].content
        print(f"🔍 Qdrant retrieval needed for query: {last_message}")
        
        # Extract potential filters from query
        filters = extract_filters_from_query(last_message)
        
        # Choose appropriate retrieval tool based on filters
        if filters:
            print(f"🎯 Using filtered retrieval with: {filters}")
            llm_with_tools = llm.bind_tools([retrieve_with_filters])
        else:
            llm_with_tools = llm.bind_tools([retrieve])
        
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    else:
        print(f"💬 No retrieval needed for query: {state['messages'][-1].content}")
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

# Execute the retrieval with multiple tools
tools = ToolNode([retrieve, retrieve_with_filters])

def score_text(text: str, query_terms: list[str]) -> int:
    """Score text relevance based on query terms."""
    t = text.lower()
    return sum(t.count(q) for q in query_terms)

def pick_relevant_context(docs_content: list[str], user_question: str, max_chars: int = 5000) -> str:
    """Select the most relevant context from retrieved documents."""
    import re
    terms = [w for w in re.findall(r"\w+", user_question.lower()) if len(w) > 2]

    # slice each doc a bit so a single long chunk can't dominate
    candidates = [c[:1200] for c in docs_content if c]
    ranked = sorted(
        candidates,
        key=lambda c: score_text(c, terms),
        reverse=True
    )

    out, total = [], 0
    for c in ranked:
        if total + len(c) > max_chars: 
            break
        out.append(c)
        total += len(c)
    
    if not out and candidates:
        out = [candidates[0][:max_chars]]  # fallback
    
    return "\n\n".join(out)

# Generate a response using the retrieved content.
@time_execution
def generate(state: MessagesState):
    """Generate answer using Qdrant-retrieved context and conversation history."""
    # Get generated ToolMessages
    tool_messages = [msg for msg in state["messages"] if msg.type == "tool"]
    
    if not tool_messages:
        return {"messages": []}

    # Flatten tool message contents into text chunks
    docs_content = []
    metadata_info = []  # Track metadata for better context
    
    for tool_msg in tool_messages:
        if getattr(tool_msg, "content", None):
            content = safe_join_content(tool_msg.content)
            docs_content.append(content)
            
            # Extract metadata if available from tool call
            if hasattr(tool_msg, 'metadata'):
                metadata_info.append(str(tool_msg.metadata))

    # Get the latest user message
    human_messages = [msg for msg in state["messages"] if msg.type == "human"]
    user_question = human_messages[-1].content if human_messages else "No question found"

    # Select a compact, relevant slice of context
    compact_context = pick_relevant_context(docs_content, user_question, max_chars=5000)
    print(f"📊 Qdrant context: {len(compact_context)} chars from {len(docs_content)} documents")

    # Enhanced system prompt for enterprise context
    system_prompt = (
        "You are an expert AI/ML assistant for an enterprise organization. Use the provided context from our knowledge base to answer questions.\n\n"
        "CONTEXT GUIDELINES:\n"
        "1. Prioritize information from the provided context when relevant\n"
        "2. If context is insufficient, use your general knowledge but indicate this\n"
        "3. For technical topics, provide practical insights and examples\n"
        "4. Consider document metadata (department, type, year) when relevant\n"
        "5. Be concise but thorough for enterprise users\n\n"
        "RESPONSE FORMAT:\n"
        "- Start with a direct answer\n"
        "- Provide supporting details from context\n"
        "- Mention source relevance when appropriate\n"
        "- Suggest related topics if helpful\n\n"
        f"RETRIEVED CONTEXT:\n{compact_context}\n\n"
        "USER QUESTION: {user_question}"
    )

    # Compose prompt
    prompt = [SystemMessage(content=system_prompt), HumanMessage(content=user_question)]

    # Run LLM with optimized settings for enterprise
    response = llm.invoke(
        prompt,
        config={
            "max_tokens": 512,
            "temperature": 0.3,
            "top_p": 0.85
        }
    )
    return {"messages": [response]}

def custom_tools_condition(state: MessagesState):
    """Check if the last AI message has tool calls."""
    messages = state["messages"]
    last = messages[-1] if messages else None

    if last and last.type == "ai" and getattr(last, "tool_calls", None):
        return "tools"
    return "done"

def build_graph():
    """Build and return the Qdrant-powered agent graph."""
    graph_builder = StateGraph(MessagesState)

    # Add nodes
    graph_builder.add_node("query_or_respond", query_or_respond)
    graph_builder.add_node("tools", tools)
    graph_builder.add_node("generate", generate)
    graph_builder.add_node("done", lambda state: state)

    # Set up the workflow
    graph_builder.set_entry_point("query_or_respond")
    
    graph_builder.add_conditional_edges(
        "query_or_respond",
        custom_tools_condition,
        {"done": "done", "tools": "tools"},
    )
    
    graph_builder.add_edge("tools", "generate")
    graph_builder.add_edge("generate", "done")
    
    print("✅ Agent graph built successfully")
    return graph_builder