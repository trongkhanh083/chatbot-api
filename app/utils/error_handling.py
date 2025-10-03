from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from app.core.agent import run_agent
import logging

def validate_message(message: str) -> bool:
    """Validate user input."""
    if not message or not message.strip():
        return False
    if len(message) > 1000:
        return False
    # Add more validation as needed
    return True

def safe_run_agent(message: str, thread_id: str = "default"):
    """Wrapper for run_agent with error handling."""
    try:
        if not validate_message(message):
            raise HTTPException(status_code=400, detail="Invalid message")
        
        human_message = HumanMessage(content=message)
        return run_agent(human_message, thread_id=thread_id)
    except Exception as e:
        logging.error(f"Error in safe_run_agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")