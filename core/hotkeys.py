import keyboard
from config import load_hotkeys

_hotkey_handles = []

def unregister():
    # Unregister previously registered hotkeys
    global _hotkey_handles
    for h in list(_hotkey_handles):
        try:
            keyboard.remove_hotkey(h)
        except Exception:
            pass
    _hotkey_handles = []

def register(app, mappings=None):
    # Register global hotkeys binding to app handlers
    global _hotkey_handles
    try:
        if _hotkey_handles:
            unregister()
        hk = mappings or load_hotkeys()
        h1 = keyboard.add_hotkey(hk["fullscreen"], app._hotkey_fullscreen)
        h2 = keyboard.add_hotkey(hk["region"], app._hotkey_region)
        h3 = keyboard.add_hotkey(hk["window"], app._hotkey_window)
        _hotkey_handles = [h1, h2, h3]
    except Exception as e:
        print(f"Failed to setup hotkeys: {e}")

def re_register(app, mappings):
    # Re-register with new mappings
    register(app, mappings)