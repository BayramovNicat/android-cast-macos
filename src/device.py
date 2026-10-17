from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

COMMON_SEARCH_PATHS = (
    "/opt/homebrew/bin",
    "/usr/local/bin",
    str(Path.home() / "Library/Android/sdk/platform-tools"),
)

@functools.lru_cache(maxsize=4)
def find_binary(name: str) -> str | None:
    """Find and cache an executable on macOS."""
    found = shutil.which(name)
    if found:
        return found
    for folder in COMMON_SEARCH_PATHS:
        candidate = Path(folder) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None

def find_adb() -> str | None:
    return find_binary("adb")

def run_adb(args: list[str], timeout: int = 5) -> str | None:
    """Run an adb command safely, returning stdout on success or None."""
    adb_path = find_adb()
    if not adb_path:
        return None
    try:
        res = subprocess.run(
            [adb_path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return res.stdout.strip() if res.returncode == 0 else None
    except (subprocess.SubprocessError, OSError):
        return None

def get_connected_devices() -> list[str]:
    """Return list of active adb device endpoints."""
    out = run_adb(["devices"])
    if not out:
        return []
    devices = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices

def get_preferred_wireless_device(retries: int = 2) -> str | None:
    """
    Auto-detect the active wireless device.
    Prefers IP:port endpoint, then mDNS target, then any attached device.
    """
    for _ in range(retries):
        devices = get_connected_devices()
        if devices:
            # 1. Prefer direct IP:port (e.g. 192.168.0.3:40957)
            for d in devices:
                if ":" in d and not d.startswith("adb-"):
                    return d
            # 2. Prefer mDNS target
            for d in devices:
                if d.startswith("adb-"):
                    return d
            return devices[0]
        time.sleep(1)
    return None

def connect_device(ip_port: str) -> bool:
    """Connect to a device endpoint via adb connect."""
    out = run_adb(["connect", ip_port], timeout=10)
    return bool(out and "connected" in out.lower())

def is_device_locked(device_serial: str) -> bool:
    """Check if the Android device is currently locked."""
    out = run_adb(["-s", device_serial, "shell", "dumpsys", "trust"], timeout=4)
    return bool(out and ("deviceLocked=1" in out or "deviceLocked=true" in out))

@functools.lru_cache(maxsize=4)
def get_screen_size(device_serial: str) -> tuple[int, int]:
    """Get the physical screen resolution of the Android device."""
    out = run_adb(["-s", device_serial, "shell", "wm", "size"], timeout=3)
    if out:
        match = re.search(r"(\d+)x(\d+)", out)
        if match:
            return int(match.group(1)), int(match.group(2))
    return 1080, 2400

def unlock_device(device_serial: str, pin: str) -> bool:
    """
    Atomically unlock the Android device in a single ADB shell execution:
    1. Wake screen (KEYCODE_WAKEUP 224)
    2. Dynamic swipe up based on screen resolution
    3. Input PIN
    4. Confirm with Enter (KEYCODE_ENTER 66)
    """
    if not pin:
        return False
    width, height = get_screen_size(device_serial)
    center_x = width // 2
    start_y = int(height * 0.75)
    end_y = int(height * 0.35)
    safe_pin = pin.replace("\\", "\\\\").replace('"', '\\"')

    compound_cmd = (
        f"input keyevent 224 && "
        f"sleep 0.7 && "
        f"input swipe {center_x} {start_y} {center_x} {end_y} 250 && "
        f"sleep 0.7 && "
        f'input text "{safe_pin}" && '
        f"sleep 0.2 && "
        f"input keyevent 66"
    )
    return run_adb(["-s", device_serial, "shell", compound_cmd], timeout=8) is not None

def gui_alert(message: str, buttons: list[str] = ["Cancel", "OK"], default: str = "OK") -> str:
    """Display a native macOS dialog using AppleScript."""
    btn_str = ", ".join(f'"{b}"' for b in buttons)
    script = (
        f'set res to display dialog "{message}" '
        f'buttons {{{btn_str}}} default button "{default}" '
        f'with title "Android Cast" with icon note\n'
        f'return button returned of res'
    )
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""

def gui_prompt(message: str, default_text: str = "") -> str | None:
    """Display a native macOS text input dialog using AppleScript."""
    script = (
        f'set res to display dialog "{message}" '
        f'default answer "{default_text}" '
        f'buttons {{"Cancel", "Connect"}} default button "Connect" '
        f'with title "Android Cast"\n'
        f'return text returned of res'
    )
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return res.stdout.strip() if res.returncode == 0 else None
    except (subprocess.SubprocessError, OSError):
        return None

