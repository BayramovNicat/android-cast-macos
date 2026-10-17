from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

def load_env(env_path: Path | None = None) -> None:
    """Loads environment variables from a .env file into os.environ."""
    candidates = (
        [env_path]
        if env_path is not None
        else [
            Path(__file__).resolve().parent.parent / ".env",
            Path(__file__).parent / ".env",
            Path.home() / ".android_cast.env",
            Path.home() / ".env",
        ]
    )

    for p in candidates:
        if p.is_file():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip().strip('"\''))
                break
            except OSError:
                pass

def get_android_pin() -> str | None:
    """Get the Android unlock PIN/password from environment or .env."""
    load_env()
    return os.getenv("ANDROID_PIN") or os.getenv("ANDROID_PASSWORD")


@dataclass(frozen=True)
class StreamConfig:
    name: str
    description: str
    bit_rate: str = "4M"
    max_size: int | None = 1200
    max_fps: int | None = None
    video_buffer_ms: int = 20
    turn_screen_off: bool = True
    power_off_on_close: bool = True
    stay_awake: bool = True
    control: bool = True
    audio: bool = True
    render_driver: str = "metal"
    video_codec: str = "h265"
    audio_codec: str = "opus"
    audio_bit_rate: str = "128K"


PROFILES: dict[str, StreamConfig] = {
    "battery": StreamConfig(
        name="Battery Saver",
        description="Physical phone screen OFF, 60 FPS, 2.5 Mbps (~75% phone power savings)",
        bit_rate="2.5M",
        max_fps=60,
        video_buffer_ms=30,
    ),
    "balanced": StreamConfig(
        name="Balanced (Default)",
        description="Native refresh rate (up to 90/120Hz), 4 Mbps, screen OFF, Metal VSync",
        bit_rate="4M",
        video_buffer_ms=20,
    ),
    "performance": StreamConfig(
        name="Ultra Performance",
        description="High bitrate (6 Mbps), phone screen stays lit, minimal buffer",
        bit_rate="6M",
        max_size=1600,
        video_buffer_ms=15,
        turn_screen_off=False,
        power_off_on_close=False,
    ),
}

DEFAULT_PROFILE = "balanced"

