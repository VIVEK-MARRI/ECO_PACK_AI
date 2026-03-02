"""
Production-grade structured logging for ECO_PACK_AI
"""

import logging
import sys
import json
import time
from datetime import datetime
from functools import wraps
import traceback

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            log_obj['traceback'] = traceback.format_exc()
        
        # Add custom fields if present
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'latency_ms'):
            log_obj['latency_ms'] = record.latency_ms
        if hasattr(record, 'model_name'):
            log_obj['model_name'] = record.model_name
        if hasattr(record, 'input_shape'):
            log_obj['input_shape'] = record.input_shape
        
        return json.dumps(log_obj)

def setup_logger(name, log_file='backend.log', level=logging.INFO):
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = JSONFormatter()
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_inference(model_name):
    """Decorator to log model inference with timing"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)
            
            start_time = time.time()
            request_id = kwargs.get('request_id', 'unknown')
            
            try:
                logger.info(
                    f"Starting inference with {model_name}",
                    extra={
                        'request_id': request_id,
                        'model_name': model_name
                    }
                )
                
                result = f(*args, **kwargs)
                
                latency_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"Inference completed for {model_name}",
                    extra={
                        'request_id': request_id,
                        'model_name': model_name,
                        'latency_ms': f"{latency_ms:.2f}"
                    }
                )
                
                return result
            
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Inference failed for {model_name}: {str(e)}",
                    extra={
                        'request_id': request_id,
                        'model_name': model_name,
                        'latency_ms': f"{latency_ms:.2f}"
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator

# Initialize global logger
logger = setup_logger('ecopackai_backend')
