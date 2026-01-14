# Production logging configuration
import logging
import sys
from datetime import datetime

# Configure structured logging for production
def setup_logging():
    """Setup production logging with structured format"""
    
    # Create logger
    logger = logging.getLogger('stirling_chat')
    logger.setLevel(logging.INFO)
    
    # Console handler with structured format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Structured formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

# Log important events
def log_request(request, response_time=None, error=None):
    """Log API requests with context"""
    logger = logging.getLogger('stirling_chat.requests')
    
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'method': request.method,
        'path': request.url.path,
        'status': 'error' if error else 'success'
    }
    
    if response_time:
        log_data['response_time_ms'] = response_time
    
    if error:
        log_data['error'] = str(error)
        logger.error(f"Request failed: {log_data}")
    else:
        logger.info(f"Request completed: {log_data}")

# Usage in main.py
# log_request(request, response_time=0.5)
