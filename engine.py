from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from config import StreamConfig, PROFILES, DEFAULT_PROFILE
from device import find_adb, get_preferred_wireless_device

COMMON_SCRCPY_PATHS = [
    "/opt/homebrew/bin/scrcpy",
    "/usr/local/bin/scrcpy",
]

def find_scrcpy() -> str | None:
    found = shutil.which("scrcpy")
    if found:
        return found
    for p in COMMON_SCRCPY_PATHS:
        path_obj = Path(p)
        if path_obj.is_file() and os.access(path_obj, os.X_OK):
            return str(path_obj)
    return None

def build_scrcpy_command(
    device_serial: str,
    config: StreamConfig,
    scrcpy_bin: str | None = None,
    custom_title: str | None = None,
) -> list[str]:
    """Constructs the optimized command array for scrcpy."""
    bin_path = scrcpy_bin or find_scrcpy() or "scrcpy"
    title = custom_title or f"Android Cast ({config.name})"

    cmd = [
        bin_path,
        "-s", device_serial,
        f"--window-title={title}",
        f"--video-codec={config.video_codec}",
        f"--video-bit-rate={config.bit_rate}",
        f"--video-buffer={config.video_buffer_ms}",
        f"--render-driver={config.render_driver}",
    ]

    if config.max_size:
        cmd.append(f"--max-size={config.max_size}")

    if config.max_fps:
        cmd.append(f"--max-fps={config.max_fps}")

    # Control vs view-only
    if config.control:
        if config.stay_awake:
            cmd.append("--stay-awake")
    else:
        cmd.append("--no-control")

    # Battery saving features
    if config.turn_screen_off and config.control:
        cmd.append("--turn-screen-off")

    if config.power_off_on_close and config.control:
        cmd.append("--power-off-on-close")

    # Audio forwarding
    if not config.audio:
        cmd.append("--no-audio")

    return cmd

def launch_stream(
    device_serial: str,
    profile_name: str = DEFAULT_PROFILE,
    override_control: bool | None = None,
    override_screen_off: bool | None = None,
) -> int:
    """Launches the screen mirror stream with the specified profile."""
    scrcpy_path = find_scrcpy()
    if not scrcpy_path:
        print("❌ scrcpy is not installed. Run: brew install scrcpy")
        return 1

    base_config = PROFILES.get(profile_name, PROFILES[DEFAULT_PROFILE])

    # Allow runtime overrides if requested
    config = base_config
    if override_control is not None or override_screen_off is not None:
        config = StreamConfig(
            name=base_config.name,
            description=base_config.description,
            video_codec=base_config.video_codec,
            bit_rate=base_config.bit_rate,
            max_size=base_config.max_size,
            max_fps=base_config.max_fps,
            video_buffer_ms=base_config.video_buffer_ms,
            turn_screen_off=override_screen_off if override_screen_off is not None else base_config.turn_screen_off,
            power_off_on_close=base_config.power_off_on_close,
            stay_awake=base_config.stay_awake,
            control=override_control if override_control is not None else base_config.control,
            audio=base_config.audio,
            render_driver=base_config.render_driver,
        )

    cmd = build_scrcpy_command(device_serial, config, scrcpy_bin=scrcpy_path)
    
    print(f"\n🚀 Launching Android Cast [{config.name}]")
    print(f"📱 Target Device : {device_serial}")
    print(f"🔋 Screen-Off    : {'Enabled (~70% battery savings)' if config.turn_screen_off else 'Disabled'}")
    print(f"🎮 Interaction   : {'Full Control (Clicking & Typing)' if config.control else 'View-Only'}")
    print(f"🖥️ Render Driver : Apple Metal (Hardware VSync)")
    print("-" * 55)

    try:
        proc = subprocess.run(cmd)
        return proc.returncode
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"❌ Error running stream: {e}")
        return 1
