from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage
from app.core.graph import build_graph
from typing import AsyncIterator, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Initialize memory
memory = MemorySaver()

# Build and compile the Qdrant-powered graph
graph_builder = build_graph()
graph = graph_builder.compile(checkpointer=memory)

def safe_convert_to_string(content):
    """Safely convert any content to a string."""
    if content is None:
        return "No response generated"
    
    if isinstance(content, str):
        return content
    
    if isinstance(content, list):
        try:
            # Handle nested lists
            flattened = []
            for item in content:
                if isinstance(item, list):
                    flattened.extend(item)
                else:
                    flattened.append(item)
            
            # Try to join if all items are strings
            if all(isinstance(item, str) for item in flattened):
                return ' '.join(flattened)
            else:
                # Convert each item to string first
                return ' '.join(str(item) for item in flattened)
        except Exception as e:
            logger.error(f"Error converting list to string: {e}")
            return str(content)
    
    # For any other type, try to convert to string
    try:
        return str(content)
    except Exception as e:
        logger.error(f"Error converting to string: {e}")
        return "Unable to process response"

def run_agent_debug(message, thread_id="qdrant_thread"):
    """Debug function to run agent and inspect Qdrant retrieval."""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Collect all messages from the stream
    all_messages = []
    for step in graph.stream(
        {"messages": [message]},
        stream_mode="values",
        config=config,
    ):  
        if step.get("messages"):
            messages = step["messages"]
            if isinstance(messages, list):
                all_messages.extend(messages)
            else:
                all_messages.append(messages)
    
    # Debug: print all messages and their content types
    print("=== AGENT DEBUG ===")
    for i, msg in enumerate(all_messages):
        print(f"Message {i}: {type(msg)}")
        print(f"Type: {msg.type}")
        print(f"Content: {msg.content}")
        print(f"Content type: {type(msg.content)}")
        
        # Show tool calls if present
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"Tool calls: {msg.tool_calls}")
        
        # Show metadata if present
        if hasattr(msg, 'metadata') and msg.metadata:
            print(f"Metadata: {msg.metadata}")
            
        print("---")
    
    # Find the last AI message in the response
    for msg in reversed(all_messages):
        if isinstance(msg, AIMessage):
            content = msg.content
            
            print(f"🎯 Final AI message content: {content}")
            print(f"Content type: {type(content)}")
            
            if isinstance(content, list):
                print("Content is a list, converting to string...")
                try:
                    if all(isinstance(item, str) for item in content):
                        content = ' '.join(content)
                    else:
                        content = ' '.join(str(item) for item in content)
                    print(f"Converted content: {content}")
                except Exception as e:
                    print(f"Error converting content: {e}")
                    content = str(content)
            
            return AIMessage(content=content)
    
    return None

def run_agent(message, thread_id="qdrant_thread"):
    """Run the Qdrant-powered agent with a message and return the AI response."""
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Collect all messages from the stream
        all_messages = []
        for step in graph.stream(
            {"messages": [message]},
            stream_mode="values",
            config=config,
        ):  
            if step.get("messages"):
                all_messages.extend(step["messages"])
        
        # Find the last AI message in the response
        for msg in reversed(all_messages):
            if isinstance(msg, AIMessage):
                logger.info(f"✅ Qdrant agent response generated successfully")
                return msg
        
        logger.warning("❌ No AI message found in response")
        return AIMessage(content="I apologize, but I couldn't generate a response. Please try again.")
    
    except Exception as e:
        logger.error(f"❌ Error in Qdrant agent invocation: {e}")
        return AIMessage(content="Sorry, I encountered an error while processing your request with our knowledge base.")

async def run_agent_stream(message: HumanMessage, thread_id: str = "qdrant_thread") -> AsyncIterator[Dict[str, Any]]:
    """Streaming version of the Qdrant-powered agent."""
    config = {"configurable": {"thread_id": thread_id}}
    
    sent_hashes = set()
    last_content = ""

    try:
        yield {"type": "status", "status": "thinking"}

        async for event in graph.astream(
            {"messages": [message]},
            config=config,
            stream_mode="values"
        ):
            if "messages" in event:
                for msg in event["messages"]:
                    if isinstance(msg, AIMessage) and hasattr(msg, 'content'):
                        content = str(msg.content).strip()
                        msg_hash = hash(content)

                        # Skip if already sent
                        if not content or msg_hash in sent_hashes or content == last_content:
                            continue
                        
                        sent_hashes.add(msg_hash)
                        last_content = content
                        yield {"type": "content", "content": content}

                    elif msg.type == "tool":
                        yield {"type": "status", "status": "searching_knowledge_base"}

        yield {"type": "status", "status": "complete"}

    except Exception as e:
        logger.error(f"❌ Error in Qdrant agent stream: {e}")
        yield {"type": "error", "error": str(e)}
