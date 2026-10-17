from __future__ import annotations

import functools
import os
import shutil
import subprocess
import time
from pathlib import Path

COMMON_SEARCH_PATHS = [
    "/opt/homebrew/bin/adb",
    "/usr/local/bin/adb",
    Path.home() / "Library/Android/sdk/platform-tools/adb",
]

@functools.lru_cache(maxsize=1)
def find_adb() -> str | None:
    """Find and cache the adb executable on macOS."""
    found = shutil.which("adb")
    if found:
        return found
    for p in COMMON_SEARCH_PATHS:
        path_obj = Path(p)
        if path_obj.is_file() and os.access(path_obj, os.X_OK):
            return str(path_obj)
    return None

def get_connected_devices(adb_bin: str | None = None) -> list[str]:
    """Return list of active adb device serials/endpoints."""
    adb_path = adb_bin or find_adb()
    if not adb_path:
        return []

    try:
        output = subprocess.check_output([adb_path, "devices"], text=True, timeout=5)
        lines = output.strip().splitlines()[1:]
        devices = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices
    except Exception:
        return []

def get_preferred_wireless_device(adb_bin: str | None = None, retries: int = 2) -> str | None:
    """
    Auto-detect the active wireless device.
    Prefers IP:port target, then mDNS target, then any attached device.
    """
    for _ in range(retries):
        devices = get_connected_devices(adb_bin)
        if devices:
            # 1. Look for direct IP:port (e.g. 192.168.0.3:40957)
            for d in devices:
                if ":" in d and not d.startswith("adb-"):
                    return d
            # 2. Look for mDNS target
            for d in devices:
                if d.startswith("adb-"):
                    return d
            return devices[0]
        time.sleep(1)
    return None

def connect_device(ip_port: str, adb_bin: str | None = None) -> bool:
    """Connect to a device endpoint via adb connect."""
    adb_path = adb_bin or find_adb()
    if not adb_path:
        return False
    try:
        res = subprocess.run([adb_path, "connect", ip_port], capture_output=True, text=True, timeout=10)
        return "connected" in res.stdout.lower()
    except Exception:
        return False

def is_device_locked(device_serial: str, adb_bin: str | None = None) -> bool:
    """Check if the Android device is currently locked."""
    adb_path = adb_bin or find_adb()
    if not adb_path:
        return False
    try:
        output = subprocess.check_output(
            [adb_path, "-s", device_serial, "shell", "dumpsys", "trust"],
            text=True,
            timeout=4,
        )
        return "deviceLocked=1" in output or "deviceLocked=true" in output
    except Exception:
        return False

@functools.lru_cache(maxsize=4)
def get_screen_size(device_serial: str, adb_bin: str | None = None) -> tuple[int, int]:
    """Get the physical screen resolution of the Android device (cached per device)."""
    adb_path = adb_bin or find_adb()
    if adb_path:
        try:
            output = subprocess.check_output(
                [adb_path, "-s", device_serial, "shell", "wm", "size"],
                text=True,
                timeout=3,
            )
            for part in output.split():
                if "x" in part and part.replace("x", "").isdigit():
                    w, h = part.split("x")
                    return int(w), int(h)
        except Exception:
            pass
    return 1080, 2400

def unlock_device(device_serial: str, pin: str, adb_bin: str | None = None) -> bool:
    """
    Atomically unlock the Android device in a single ADB shell execution:
    1. Wakes up the screen (224 / KEYCODE_WAKEUP)
    2. Swipes up dynamically based on screen resolution to reveal PIN keypad
    3. Types the PIN or password
    4. Confirms with Enter (66 / KEYCODE_ENTER)
    """
    adb_path = adb_bin or find_adb()
    if not adb_path or not pin:
        return False
    try:
        width, height = get_screen_size(device_serial, adb_path)
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

        res = subprocess.run(
            [adb_path, "-s", device_serial, "shell", compound_cmd],
            timeout=8,
            capture_output=True,
            text=True,
        )
        return res.returncode == 0
    except Exception as e:
        print(f"⚠️ Failed to unlock device: {e}")
        return False

