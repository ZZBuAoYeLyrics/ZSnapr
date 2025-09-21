import os
import json
from pathlib import Path

# Application configuration
APP_NAME = "ZSnapr"
APP_VERSION = "1.0.2"
APP_CHANNEL = "Pre-Release"

# Default save directory
DEFAULT_SAVE_DIR = os.path.join(Path.home(), "Pictures", "ZSnapr")

# Supported image formats
SUPPORTED_FORMATS = [
    {"name": "PNG", "extension": ".png"},
    {"name": "JPEG", "extension": ".jpg"},
    {"name": "BMP", "extension": ".bmp"},
    {"name": "TIFF", "extension": ".tiff"}
]

# Default settings
DEFAULT_SETTINGS = {
    "save_directory": DEFAULT_SAVE_DIR,
    "image_format": "PNG",
    "auto_save": True,
    "show_cursor": False,
    "delay_seconds": 0,
    "auto_copy_fullscreen": False,
    "auto_copy_window": False
}

# Hotkeys
HOTKEYS = {
    "fullscreen": "ctrl+shift+f",
    "region": "ctrl+shift+r",
    "window": "ctrl+shift+w"
}

CONFIG_DIR = os.path.join("assets", "config")
HOTKEYS_FILE = os.path.join(CONFIG_DIR, "hotkeys.json")

def load_hotkeys():
    # Load hotkeys from file and merge into HOTKEYS
    try:
        if os.path.exists(HOTKEYS_FILE):
            with open(HOTKEYS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k in ("fullscreen", "region", "window"):
                    v = data.get(k)
                    if isinstance(v, str) and v.strip():
                        HOTKEYS[k] = v.strip()
    except Exception:
        pass
    return HOTKEYS

def save_hotkeys(hotkeys: dict):
    # Persist hotkeys to file and update in-memory defaults
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        data = {k: str(hotkeys.get(k, HOTKEYS.get(k, ""))).strip() for k in ("fullscreen", "region", "window")}
        with open(HOTKEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        for k, v in data.items():
            if v:
                HOTKEYS[k] = v
    except Exception:
        pass

try:
    load_hotkeys()
except Exception:
    pass