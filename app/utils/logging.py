import logging
import sys
from datetime import datetime
import json

def setup_logging():
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/chatbot_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

class ChatLogger:
    def __init__(self):
        self.logger = setup_logging()
    
    def log_chat(self, thread_id: str, user_message: str, ai_response: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "thread_id": thread_id,
            "user_message": user_message,
            "ai_response": ai_response
        }
        self.logger.info(f"CHAT_LOG: {json.dumps(log_entry)}")