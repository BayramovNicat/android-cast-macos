from __future__ import annotations

from dataclasses import replace
import subprocess
from config import StreamConfig, PROFILES, DEFAULT_PROFILE
from device import find_binary

def find_scrcpy() -> str | None:
    """Find and cache the scrcpy executable on macOS."""
    return find_binary("scrcpy")

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
        if config.turn_screen_off:
            cmd.append("--turn-screen-off")
        if config.power_off_on_close:
            cmd.append("--power-off-on-close")
    else:
        cmd.append("--no-control")

    # Audio forwarding
    if config.audio:
        cmd.extend([
            f"--audio-codec={config.audio_codec}",
            f"--audio-bit-rate={config.audio_bit_rate}",
        ])
    else:
        cmd.append("--no-audio")

    return cmd

def launch_stream(
    device_serial: str,
    profile_name: str = DEFAULT_PROFILE,
    override_control: bool | None = None,
    override_screen_off: bool | None = None,
    override_audio: bool | None = None,
) -> int:
    """Launches the screen mirror stream with the specified profile."""
    scrcpy_path = find_scrcpy()
    if not scrcpy_path:
        print("❌ scrcpy is not installed. Run: brew install scrcpy")
        return 1

    base_config = PROFILES.get(profile_name, PROFILES[DEFAULT_PROFILE])

    # Apply any explicit command-line overrides
    overrides: dict[str, bool] = {}
    if override_control is not None:
        overrides["control"] = override_control
    if override_screen_off is not None:
        overrides["turn_screen_off"] = override_screen_off
    if override_audio is not None:
        overrides["audio"] = override_audio

    config = replace(base_config, **overrides) if overrides else base_config
    cmd = build_scrcpy_command(device_serial, config, scrcpy_bin=scrcpy_path)

    print(f"\n🚀 Launching Android Cast [{config.name}]")
    print(f"📱 Target Device : {device_serial}")
    print(f"🔊 Audio Forward : {'Enabled (' + config.audio_codec.upper() + ' ' + config.audio_bit_rate + ')' if config.audio else 'Disabled'}")
    print(f"🔋 Screen-Off    : {'Enabled (~75% battery savings)' if config.turn_screen_off else 'Disabled'}")
    print(f"🎮 Interaction   : {'Full Control (Touch & Type)' if config.control else 'View-Only'}")
    print(f"🖥️ Render Driver : Apple Metal (Hardware VSync)")
    print("-" * 55)

    try:
        proc = subprocess.run(cmd)
        return proc.returncode
    except KeyboardInterrupt:
        return 0
    except OSError as e:
        print(f"❌ Error running stream: {e}")
        return 1

