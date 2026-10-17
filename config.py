from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

def load_env(env_path: Path | None = None) -> None:
    """Loads environment variables from a .env file."""
    if env_path is None:
        # Check current project directory and user home
        candidates = [
            Path(__file__).parent / ".env",
            Path.home() / ".android_cast.env",
            Path.home() / ".env",
        ]
    else:
        candidates = [env_path]

    for p in candidates:
        if p.is_file():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ.setdefault(key, val)
                break
            except Exception:
                pass

def get_android_pin() -> str | None:
    """Get the Android unlock PIN/password from environment or .env."""
    load_env()
    return os.getenv("ANDROID_PIN") or os.getenv("ANDROID_PASSWORD")


@dataclass(frozen=True)
class StreamConfig:
    name: str
    description: str
    video_codec: str
    bit_rate: str
    max_size: int | None
    max_fps: int | None
    video_buffer_ms: int
    turn_screen_off: bool
    power_off_on_close: bool
    stay_awake: bool
    control: bool
    audio: bool
    render_driver: str

# Pre-tuned profiles optimized for Android and Mac
PROFILES: dict[str, StreamConfig] = {
    "battery": StreamConfig(
        name="Battery Saver",
        description="Physical phone screen turned OFF, hardware H.265, 60 FPS, lowest battery draw (~70% savings)",
        video_codec="h265",
        bit_rate="2.5M",
        max_size=1200,
        max_fps=60,
        video_buffer_ms=30,
        turn_screen_off=True,
        power_off_on_close=True,
        stay_awake=True,
        control=True,
        audio=False,
        render_driver="metal",
    ),
    "balanced": StreamConfig(
        name="Balanced (Default)",
        description="Smooth 90 Hz native display, hardware H.265, Metal VSync, phone screen off",
        video_codec="h265",
        bit_rate="4M",
        max_size=1200,
        max_fps=None,  # Native 90 Hz
        video_buffer_ms=20,
        turn_screen_off=True,
        power_off_on_close=True,
        stay_awake=True,
        control=True,
        audio=False,
        render_driver="metal",
    ),
    "performance": StreamConfig(
        name="Ultra Performance",
        description="Uncapped 90 Hz, high bitrate, phone screen stays illuminated",
        video_codec="h265",
        bit_rate="6M",
        max_size=1600,
        max_fps=None,
        video_buffer_ms=15,
        turn_screen_off=False,
        power_off_on_close=False,
        stay_awake=True,
        control=True,
        audio=False,
        render_driver="metal",
    ),
}

DEFAULT_PROFILE = "balanced"
