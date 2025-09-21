import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import threading
import traceback
import atexit

class Logger:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Create logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('ZSnapr')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        log_file = self.log_dir / f"zSnapr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(threadName)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.info("Logger initialized")
        
        # Schedule silent automatic log cleanup on exit only
        self._schedule_silent_cleanup()
    
    def _schedule_silent_cleanup(self):
        # Schedule silent automatic log cleanup on application exit only
        def silent_cleanup_on_exit():
            try:
                from core.log_sys.auto_clean import auto_cleanup_logs, CleanupStrategy
                result = auto_cleanup_logs(CleanupStrategy.AGGRESSIVE)
                
                if result.get("status") == "success":
                    deleted_count = len(result.get("deleted_files", []))
                    files_before = result.get("files_before", 0)
                    files_after = result.get("files_after", 0)
                    mb_freed = result.get("mb_freed", 0)
                    
                    if deleted_count > 0:
                        self.info(f"Exit cleanup completed: deleted {deleted_count} old log files")
                        self.info(f"Before cleanup: {files_before} files, after cleanup: {files_after} files")
                        if mb_freed > 0:
                            self.info(f"Space freed: {mb_freed:.2f} MB")
                    else:
                        self.info("Exit cleanup check: no files need to be deleted")
                elif result.get("status") == "no_cleanup_needed":
                    self.info("Exit cleanup check: log file count is normal, no cleanup needed")
                else:
                    self.warning(f"Exit cleanup status: {result.get('status', 'unknown')}")
            except Exception as e:
                self.error(f"Exception in silent cleanup: {e}")
        
        atexit.register(silent_cleanup_on_exit)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)
    
    def exception(self, message):
        self.logger.exception(message)
    
    def log_function_entry(self, func_name, args=None, kwargs=None):
        # Log function entry with parameters
        params = []
        if args:
            params.append(f"args={args}")
        if kwargs:
            params.append(f"kwargs={kwargs}")
        param_str = ", ".join(params) if params else "no params"
        self.debug(f"ENTER {func_name}({param_str})")
    
    def log_function_exit(self, func_name, result=None):
        # Log function exit with result
        result_str = f"result={result}" if result is not None else "no result"
        self.debug(f"EXIT {func_name} -> {result_str}")
    
    def log_thread_info(self, message):
        # Log with thread information
        thread_name = threading.current_thread().name
        thread_id = threading.get_ident()
        self.debug(f"[Thread:{thread_name}:{thread_id}] {message}")
    
    def log_qt_event(self, event_type, details=None):
        # Log Qt events
        details_str = f" - {details}" if details else ""
        self.debug(f"QT_EVENT: {event_type}{details_str}")
    
    def log_hotkey_event(self, hotkey, action):
        # Log hotkey events
        self.info(f"HOTKEY: {hotkey} -> {action}")
    
    def log_screenshot_event(self, event_type, details=None):
        # Log screenshot events
        details_str = f" - {details}" if details else ""
        self.info(f"SCREENSHOT: {event_type}{details_str}")
    
    def log_tray_event(self, event_type, details=None):
        # Log tray events
        details_str = f" - {details}" if details else ""
        self.info(f"TRAY: {event_type}{details_str}")

# Global logger instance
_logger_instance = None

def get_logger():
    # Get global logger instance
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance

# Decorator for function logging
def log_function(func):
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.log_function_entry(func.__name__, args, kwargs)
        try:
            result = func(*args, **kwargs)
            logger.log_function_exit(func.__name__, result)
            return result
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            logger.exception("Full traceback:")
            raise
    return wrapper

# Context manager for operation logging
class LogOperation:
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.logger = get_logger()
    
    def __enter__(self):
        self.logger.info(f"START OPERATION: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"OPERATION FAILED: {self.operation_name} - {exc_val}")
            self.logger.exception("Operation exception:")
        else:
            self.logger.info(f"OPERATION COMPLETED: {self.operation_name}")