import io
from PIL import Image
import win32clipboard

class ClipboardManager:
    """Clipboard operations for screenshots"""
    
    @staticmethod
    def copy_image_to_clipboard(image):
        """Copy PIL Image to Windows clipboard"""
        try:
            # Convert PIL image to bytes
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # Remove BMP header
            output.close()
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            return True
        except Exception as e:
            print(f"Clipboard copy error: {e}")
            return False
    
    @staticmethod
    def copy_file_to_clipboard(filepath):
        """Copy file path to clipboard"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(filepath)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print(f"File path copy error: {e}")
            return False