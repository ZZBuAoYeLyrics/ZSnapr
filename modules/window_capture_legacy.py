import win32gui
import win32ui
import win32con
from PIL import Image
import pyautogui

class WindowCapture:
    """Active window capture functionality"""
    
    @staticmethod
    def get_active_window_rect():
        """Get the rectangle of the active window"""
        try:
            # Get the active window handle
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None
            
            # Get window rectangle
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None
    
    @staticmethod
    def capture_active_window():
        """Capture the active window"""
        try:
            rect = WindowCapture.get_active_window_rect()
            if rect is None:
                # Fallback to full screen
                return pyautogui.screenshot()
            
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            # Ensure valid dimensions
            if width <= 0 or height <= 0:
                return pyautogui.screenshot()
            
            # Capture the window region
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return screenshot
            
        except Exception as e:
            print(f"Window capture error: {e}")
            # Fallback to full screen
            return pyautogui.screenshot()
    
    @staticmethod
    def get_window_title():
        """Get the title of the active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return "Unknown Window"
            
            title = win32gui.GetWindowText(hwnd)
            return title if title else "Untitled Window"
        except Exception as e:
            return "Unknown Window"