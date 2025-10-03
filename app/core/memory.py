from app.core.agent import graph

def get_conversation_history(thread_id: str):
    """Get conversation history for a thread."""
    try:
        # Get the current state from the graph's memory
        config = {"configurable": {"thread_id": thread_id}}
        current_state = graph.get_state(config)
        return current_state.values.get("messages", [])
    except:
        return []

def clear_conversation_history(thread_id: str):
    """Clear conversation history for a thread."""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        graph.update_state(config, {"messages": []})
        return True
    except:
        return False