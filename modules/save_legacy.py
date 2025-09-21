import os
from datetime import datetime
from tkinter import filedialog
import tkinter as tk
from PIL import Image

class SaveManager:
    """File save operations for screenshots"""
    
    def __init__(self, default_directory):
        self.default_directory = default_directory
        
    def save_as_dialog(self, image, initial_filename=None):
        """Show save as dialog and save image"""
        try:
            # Create hidden root window
            root = tk.Tk()
            root.withdraw()
            
            if initial_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                initial_filename = f"screenshot_{timestamp}.png"
            
            # Show save dialog
            filepath = filedialog.asksaveasfilename(
                initialdir=self.default_directory,
                initialfile=initial_filename,
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("BMP files", "*.bmp"),
                    ("TIFF files", "*.tiff"),
                    ("All files", "*.*")
                ]
            )
            
            root.destroy()
            
            if filepath:
                # Determine format from extension
                ext = os.path.splitext(filepath)[1].lower()
                if ext == '.jpg' or ext == '.jpeg':
                    # Convert RGBA to RGB for JPEG
                    if image.mode == "RGBA":
                        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                        rgb_image.paste(image, mask=image.split()[-1])
                        image = rgb_image
                    image.save(filepath, "JPEG", quality=95)
                else:
                    image.save(filepath)
                
                return filepath
            
            return None
            
        except Exception as e:
            print(f"Save as error: {e}")
            return None
    
    def quick_save(self, image, directory, format_name="PNG"):
        """Quick save with auto-generated filename"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get extension based on format
            extensions = {
                "PNG": ".png",
                "JPEG": ".jpg", 
                "BMP": ".bmp",
                "TIFF": ".tiff"
            }
            
            ext = extensions.get(format_name, ".png")
            filename = f"screenshot_{timestamp}{ext}"
            filepath = os.path.join(directory, filename)
            
            # Ensure directory exists
            os.makedirs(directory, exist_ok=True)
            
            # Save image
            if format_name == "JPEG":
                if image.mode == "RGBA":
                    rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[-1])
                    image = rgb_image
                image.save(filepath, "JPEG", quality=95)
            else:
                image.save(filepath, format_name)
            
            return filepath
            
        except Exception as e:
            print(f"Quick save error: {e}")
            return None