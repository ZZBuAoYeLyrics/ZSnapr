import os
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '0'
os.environ['QT_SCALE_FACTOR'] = '1'
os.environ['QT_SCREEN_SCALE_FACTORS'] = '1'
os.environ['QT_DEVICE_PIXEL_RATIO'] = '1'

import pyautogui
import time
from PIL import Image
from datetime import datetime
from config import DEFAULT_SAVE_DIR, SUPPORTED_FORMATS
from modules.window_capture_legacy import WindowCapture
from core.log_sys import get_logger
import subprocess
import sys
import json
import os
import re
import tempfile

class ScreenshotEngine:
    def __init__(self):
        self.logger = get_logger()
        self.logger.debug("ScreenshotEngine.__init__")
        
        # Disable pyautogui failsafe
        pyautogui.FAILSAFE = False
        self.save_directory = DEFAULT_SAVE_DIR
        self.image_format = "PNG"
        self.auto_save = True
        self.show_cursor = False
        self.delay_seconds = 0
        
        # Ensure save directory exists
        os.makedirs(self.save_directory, exist_ok=True)
        self.logger.debug("ScreenshotEngine initialized")
    
    def set_save_directory(self, directory):
        """Set the directory where screenshots will be saved"""
        self.save_directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def set_image_format(self, format_name):
        """Set the image format for saving screenshots"""
        if format_name in [fmt["name"] for fmt in SUPPORTED_FORMATS]:
            self.image_format = format_name
    
    def set_delay(self, seconds):
        """Set delay before taking screenshot"""
        self.delay_seconds = max(0, seconds)
    
    def _apply_delay(self):
        """Apply delay if set"""
        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)
    
    def _get_file_extension(self):
        """Get file extension based on current format"""
        for fmt in SUPPORTED_FORMATS:
            if fmt["name"] == self.image_format:
                return fmt["extension"]
        return ".png"
    
    def _generate_filename(self):
        """Generate filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = self._get_file_extension()
        return f"screenshot_{timestamp}{extension}"
    
    def capture_fullscreen(self):
        """Capture full screen screenshot"""
        self._apply_delay()
        screenshot = pyautogui.screenshot()
        return screenshot
    
    def capture_region(self, x=None, y=None, width=None, height=None):
        """Capture specific region of screen"""
        self.logger.debug(f"capture_region called with x={x}, y={y}, width={width}, height={height}")
        
        action = "copy"
        if x is None or y is None or width is None or height is None:
            # Launch selector in a separate process to avoid Qt main-thread conflicts
            try:
                self.logger.debug("Spawning region_worker subprocess with temp json")
                worker_path = os.path.join(os.getcwd(), "modules", "region_worker.py")
                env = os.environ.copy()
                env.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.*=false")
                env.setdefault("QT_LOGGING_TO_CONSOLE", "0")
                with tempfile.NamedTemporaryFile(prefix="zsnapr_region_", suffix=".json", delete=False) as tf:
                    out_path = tf.name
                env["ZSNAPR_REGION_OUT"] = out_path
                cmd = [sys.executable, worker_path]
                self.logger.debug(f"tmp json path={out_path}")
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
                self.logger.debug(f"region_worker returncode={proc.returncode}")
                stdout = (proc.stdout or "").strip()
                stderr = (proc.stderr or "").strip()
                if stdout:
                    self.logger.debug(f"region_worker stdout(raw)={stdout}")
                if stderr:
                    self.logger.debug(f"region_worker stderr={stderr}")
                data = None
                try:
                    exists = os.path.exists(out_path)
                    self.logger.debug(f"tmp json exists={exists}")
                    if exists:
                        with open(out_path, "r", encoding="utf-8") as f:
                            txt = f.read().strip()
                        self.logger.debug(f"tmp json content={txt}")
                        if txt:
                            data = json.loads(txt)
                finally:
                    try:
                        if os.path.exists(out_path):
                            os.remove(out_path)
                    except Exception:
                        pass
                if not data or not data.get("ok"):
                    reason = data.get("reason") if isinstance(data, dict) else "unknown"
                    self.logger.info(f"Region selection not ok: {reason}")
                    return None
                x = int(data["x"]); y = int(data["y"]); width = int(data["w"]); height = int(data["h"])
                action = data.get("action", "copy")
                self.logger.debug(f"Worker provided region: ({x},{y},{width},{height}), action={action}")
            except subprocess.TimeoutExpired:
                self.logger.error("region_worker timed out")
                return None
            except Exception as e:
                self.logger.error(f"region_worker failed: {e}")
                self.logger.exception("region_worker exception:")
                return None
        
        self.logger.debug("Applying delay before screenshot")
        self._apply_delay()
        
        self.logger.debug(f"Taking screenshot with region: ({x}, {y}, {width}, {height})")
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        self.logger.debug(f"Screenshot taken, size: {screenshot.size}")
        
        result = (screenshot, action)
        self.logger.debug(f"Returning result: screenshot + action '{action}'")
        return result
    
    def capture_window(self):
        """Capture active window"""
        self._apply_delay()
        return WindowCapture.capture_active_window()
    
    def save_screenshot(self, screenshot, filename=None):
        """Save screenshot to file"""
        if filename is None:
            filename = self._generate_filename()
        
        filepath = os.path.join(self.save_directory, filename)
        
        # Convert format if needed
        if self.image_format == "JPEG":
            # Convert RGBA to RGB for JPEG
            if screenshot.mode == "RGBA":
                rgb_screenshot = Image.new("RGB", screenshot.size, (255, 255, 255))
                rgb_screenshot.paste(screenshot, mask=screenshot.split()[-1])
                screenshot = rgb_screenshot
        
        screenshot.save(filepath, format=self.image_format)
        return filepath
    
    def get_screen_size(self):
        """Get screen dimensions"""
        return pyautogui.size()