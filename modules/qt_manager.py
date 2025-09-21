import sys
from PySide6.QtWidgets import QApplication
from core.log_sys import get_logger

class QtManager:
    # Singleton Qt Application manager to prevent conflicts
    _instance = None
    _app = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QtManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.logger = get_logger()
        self.logger.debug("QtManager initialized")
    
    def get_application(self):
        # Get or create QApplication instance
        if self._app is None:
            self.logger.debug("Checking for existing QApplication")
            existing_app = QApplication.instance()
            
            if existing_app is None:
                self.logger.debug("Creating new QApplication")
                self._app = QApplication(sys.argv)
            else:
                self.logger.debug("Using existing QApplication")
                self._app = existing_app
        
        return self._app
    
    def cleanup(self):
        # Clean up Qt resources
        self.logger.debug("QtManager cleanup requested")
        # Don't actually quit the app, just reset our reference
        # The app will be cleaned up when the main process exits
        pass

# Global instance
_qt_manager = None

def get_qt_app():
    # Get global Qt application
    global _qt_manager
    if _qt_manager is None:
        _qt_manager = QtManager()
    return _qt_manager.get_application()