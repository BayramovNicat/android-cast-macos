from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src modules are resolvable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import PROFILES, DEFAULT_PROFILE, get_android_pin
from device import (
    get_preferred_wireless_device,
    connect_device,
    is_device_locked,
    unlock_device,
    gui_alert,
    gui_prompt,
)
from engine import launch_stream

def print_banner(device: str | None = None) -> None:
    status = ""
    if device:
        lock_str = "🔒 Locked (Auto-unlock ready)" if is_device_locked(device) else "🔓 Unlocked"
        status = f"   Device: {device} | Status: {lock_str}\n"
    print(f"""
======================================================================
       📱 Android Cast - High-Performance Wi-Fi Screen Mirror
======================================================================
{status}""")

def prompt_interactive_menu(device: str | None = None) -> tuple[str, bool, bool]:
    print_banner(device)
    print("Choose streaming mode:")
    print("  [1] Balanced Mode (Recommended: Native refresh, Screen-Off battery saving)")
    print("  [2] Maximum Battery Saver (60 FPS, 2.5 Mbps, ~75% less phone power)")
    print("  [3] Ultra Performance (High Bitrate, phone screen stays lit)")
    print("  [4] View-Only Mode (Read-only presentation, touch disabled)")
    print("  [5] Exit")

    choice = input("\nEnter choice [1-5] (default 1): ").strip() or "1"

    mapping = {
        "1": ("balanced", True, True),
        "2": ("battery", True, True),
        "3": ("performance", True, False),
        "4": ("balanced", False, False),
    }

    if choice == "5":
        sys.exit(0)
    if choice in mapping:
        return mapping[choice]

    print("Invalid choice, defaulting to Balanced.")
    return ("balanced", True, True)

def resolve_device(ip: str | None = None, is_gui: bool = False) -> str | None:
    """Finds or connects to an Android device, offering GUI alerts if headless."""
    if ip:
        print(f"Connecting to {ip}...")
        connect_device(ip)
        return ip

    print("🔍 Discovering paired phone over Wi-Fi...")
    device = get_preferred_wireless_device(retries=3)
    if device or not is_gui:
        return device

    # Headless macOS .app flow: prompt user with native AppleScript dialogs
    while not device:
        action = gui_alert(
            "No Android phone detected over Wi-Fi.\n\n"
            "Make sure your Android phone is on Wi-Fi with Wireless Debugging enabled.",
            buttons=["Cancel", "Enter IP...", "Retry"],
            default="Retry",
        )
        if action == "Retry":
            device = get_preferred_wireless_device(retries=2)
        elif action == "Enter IP...":
            custom_ip = gui_prompt(
                "Enter your phone Wireless Debugging IP & Port:\n(e.g. 192.168.0.3:40957)",
                "192.168.0.3:40957",
            )
            if custom_ip:
                connect_device(custom_ip)
                device = get_preferred_wireless_device(retries=2)
        else:
            return None

    return device

def main() -> None:
    parser = argparse.ArgumentParser(description="Android Cast - Wi-Fi Screen Mirror for macOS")
    parser.add_argument("--battery", action="store_true", help="Launch in Maximum Battery Saver mode")
    parser.add_argument("--performance", action="store_true", help="Launch in Ultra Performance mode")
    parser.add_argument("--view-only", action="store_true", help="Disable mouse/keyboard interactions")
    parser.add_argument("--screen-on", action="store_true", help="Keep physical phone screen illuminated")
    parser.add_argument("--ip", type=str, help="Specific phone IP:Port to connect")
    parser.add_argument("--pin", type=str, help="PIN or password to automatically unlock the phone")
    parser.add_argument("--no-unlock", action="store_true", help="Skip automatic lockscreen unlocking")
    parser.add_argument("--no-audio", action="store_true", help="Disable audio forwarding to Mac")
    args = parser.parse_args()

    is_gui = not sys.stdin.isatty()
    device = resolve_device(ip=args.ip, is_gui=is_gui)

    if not device:
        if not is_gui:
            print("\n❌ No Android phone detected over Wi-Fi.")
            print("Tips:")
            print("  1. Make sure your phone is connected to the same Wi-Fi network.")
            print("  2. Ensure 'Wireless debugging' is turned ON in Developer options.")
        sys.exit(1)

    profile = DEFAULT_PROFILE
    override_control = None
    override_screen_off = None

    if args.battery:
        profile = "battery"
    elif args.performance:
        profile = "performance"
    elif not is_gui and not any([args.battery, args.performance, args.view_only, args.screen_on, args.ip, args.pin]):
        profile, ctrl, scr_off = prompt_interactive_menu(device)
        override_control = ctrl
        override_screen_off = scr_off

    if args.view_only:
        override_control = False
    if args.screen_on:
        override_screen_off = False

    # Auto-unlock phone if locked
    if not args.no_unlock:
        pin = args.pin or get_android_pin()
        if is_device_locked(device):
            if pin:
                print("🔓 Phone is locked. Auto-unlocking with PIN from .env...")
                unlock_device(device, pin)
            else:
                print("ℹ️  Phone is locked. (Set ANDROID_PIN in .env to auto-unlock)")

    exit_code = launch_stream(
        device_serial=device,
        profile_name=profile,
        override_control=override_control,
        override_screen_off=override_screen_off,
        override_audio=False if args.no_audio else None,
    )
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

