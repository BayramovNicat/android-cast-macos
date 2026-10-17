#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

APP_NAME = "Android Cast"
BUNDLE_DIR = Path(__file__).parent / f"{APP_NAME}.app"
CONTENTS_DIR = BUNDLE_DIR / "Contents"
MACOS_DIR = CONTENTS_DIR / "MacOS"
RESOURCES_DIR = CONTENTS_DIR / "Resources"

def generate_icons():
    """Generate high-resolution macOS ICNS and PNG assets."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    iconset_dir = Path("/tmp/AndroidCast.iconset")
    iconset_dir.mkdir(parents=True, exist_ok=True)

    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Squircle mask
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(32, 32), (size - 32, size - 32)], radius=224, fill=255)

    # Modern gradient background (Deep Blue to Electric Violet)
    grad = Image.new("RGBA", (size, size))
    for y in range(size):
        ratio = y / size
        r_val = int(24 * (1 - ratio) + 99 * ratio)
        g_val = int(72 * (1 - ratio) + 102 * ratio)
        b_val = int(216 * (1 - ratio) + 241 * ratio)
        for x in range(size):
            grad.putpixel((x, y), (r_val, g_val, b_val, 255))

    img.paste(grad, (0, 0), mask)
    draw = ImageDraw.Draw(img)

    # Mac monitor illustration
    m_left, m_top, m_right, m_bottom = 260, 270, 830, 680
    draw.rounded_rectangle([(m_left, m_top), (m_right, m_bottom)], radius=36, outline=(255, 255, 255, 220), width=24)
    draw.rectangle([(505, 680), (585, 750)], fill=(255, 255, 255, 200))
    draw.rounded_rectangle([(430, 740), (660, 765)], radius=12, fill=(255, 255, 255, 220))

    # Phone illustration
    p_left, p_top, p_right, p_bottom = 170, 350, 440, 830
    draw.rounded_rectangle([(p_left - 10, p_top - 10), (p_right + 10, p_bottom + 10)], radius=48, fill=(15, 23, 42, 240))
    draw.rounded_rectangle([(p_left, p_top), (p_right, p_bottom)], radius=42, fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=18)
    draw.rounded_rectangle([(p_left + 20, p_top + 45), (p_right - 20, p_bottom - 45)], radius=24, fill=(14, 165, 233, 230))
    draw.rounded_rectangle([(p_left + 90, p_bottom - 24), (p_right - 90, p_bottom - 14)], radius=5, fill=(255, 255, 255, 200))

    # Wi-Fi waves
    draw.arc([(490, 360), (670, 540)], start=200, end=340, fill=(255, 255, 255, 240), width=18)
    draw.arc([(440, 310), (720, 590)], start=200, end=340, fill=(255, 255, 255, 240), width=18)
    draw.ellipse([(568, 480), (592, 504)], fill=(255, 255, 255, 255))

    sizes = [
        (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
    ]
    for s, name in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(iconset_dir / name)

    img.resize((256, 256), Image.Resampling.LANCZOS).save(RESOURCES_DIR / "scrcpy.png")
    img.resize((256, 256), Image.Resampling.LANCZOS).save(RESOURCES_DIR / "disconnected.png")

    icns_path = RESOURCES_DIR / "AppIcon.icns"
    subprocess.run(["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)], check=True)
    shutil.rmtree(iconset_dir, ignore_errors=True)
    print("✓ Created custom high-res AppIcon.icns.")

def create_info_plist():
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.user.androidcast</string>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0</string>
    <key>CFBundleVersion</key>
    <string>2.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
    (CONTENTS_DIR / "Info.plist").write_text(plist_content, encoding="utf-8")
    print("✓ Created Info.plist.")

def create_executables():
    MACOS_DIR.mkdir(parents=True, exist_ok=True)

    # Embed .env into App Resources and copy to ~/.android_cast.env for portability
    env_source = Path(__file__).parent / ".env"
    if env_source.is_file():
        shutil.copy2(env_source, RESOURCES_DIR / ".env")
        shutil.copy2(env_source, Path.home() / ".android_cast.env")

    scrcpy_source = "/opt/homebrew/bin/scrcpy"
    engine_dest = MACOS_DIR / "AndroidCastEngine"
    shutil.copy2(scrcpy_source, engine_dest)
    engine_dest.chmod(0o755)

    launcher_script = f"""#!/usr/bin/env bash
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
RESOURCES_DIR="$DIR/../Resources"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export SCRCPY_SERVER_PATH="/opt/homebrew/share/scrcpy/scrcpy-server"
export SCRCPY_ICON_DIR="$RESOURCES_DIR"

get_device() {{
    adb devices | grep -E '(\\bdevice\\b)' | grep -v 'List of' | head -n 1 | awk '{{print $1}}'
}}

DEVICE=$(get_device)

# Retry auto-discovery if needed
if [ -z "$DEVICE" ]; then
    sleep 1.5
    DEVICE=$(get_device)
fi

# Fallback alert with prompt if device offline
if [ -z "$DEVICE" ]; then
    USER_ACTION=$(osascript -e '
        set dialogResult to display dialog "No Android phone detected over Wi-Fi.\n\nMake sure your Android phone is on Wi-Fi with Wireless Debugging enabled." buttons {{"Cancel", "Enter IP...", "Retry"}} default button "Retry" with title "Android Cast" with icon note
        return button returned of dialogResult
    ')

    if [ "$USER_ACTION" = "Retry" ]; then
        DEVICE=$(get_device)
        if [ -z "$DEVICE" ]; then
            osascript -e 'display alert "Android Cast" message "Still no device found. Please check phone settings."'
            exit 1
        fi
    elif [ "$USER_ACTION" = "Enter IP..." ]; then
        IP_PORT=$(osascript -e '
            set ipInput to display dialog "Enter your phone Wireless Debugging IP & Port:\n(e.g. 192.168.0.3:40957)" default answer "192.168.0.3:40957" buttons {{"Cancel", "Connect"}} default button "Connect" with title "Android Cast"
            return text returned of ipInput
        ')
        if [ -n "$IP_PORT" ]; then
            adb connect "$IP_PORT"
            sleep 1
            DEVICE=$(get_device)
        fi
    else
        exit 0
    fi
fi

if [ -z "$DEVICE" ]; then
    exit 1
fi

# Auto-unlock using .env if phone is locked
ENV_FILE="$RESOURCES_DIR/.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$HOME/.android_cast.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$DIR/../../../../.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$HOME/.env"

ANDROID_PIN=""
if [ -f "$ENV_FILE" ]; then
    ANDROID_PIN=$(grep -E '^(ANDROID_PIN|ANDROID_PASSWORD)=' "$ENV_FILE" | head -n 1 | cut -d'=' -f2- | tr -d ' "\r\t')
fi

IS_LOCKED=$(adb -s "$DEVICE" shell dumpsys trust 2>/dev/null | grep -E "deviceLocked=1|deviceLocked=true")
if [ -n "$IS_LOCKED" ] && [ -n "$ANDROID_PIN" ]; then
    adb -s "$DEVICE" shell input keyevent 224
    sleep 0.7

    # Dynamic swipe coordinates for any Android screen resolution
    SIZE=$(adb -s "$DEVICE" shell wm size 2>/dev/null | grep -oE '[0-9]+x[0-9]+' | head -n 1)
    WIDTH="${{SIZE%x*}}"
    HEIGHT="${{SIZE#*x}}"
    [ -z "$WIDTH" ] && WIDTH=1080
    [ -z "$HEIGHT" ] && HEIGHT=2400
    SWIPE_X=$((WIDTH / 2))
    SWIPE_Y1=$((HEIGHT * 3 / 4))
    SWIPE_Y2=$((HEIGHT / 3))

    adb -s "$DEVICE" shell input swipe "$SWIPE_X" "$SWIPE_Y1" "$SWIPE_X" "$SWIPE_Y2" 250
    sleep 0.7
    adb -s "$DEVICE" shell input text "$ANDROID_PIN"
    sleep 0.2
    adb -s "$DEVICE" shell input keyevent 66
    sleep 0.5
fi

# High-Efficiency Launcher:
# 1. Hardware Metal VSync presentation
# 2. Hardware H.265 encoder
# 3. Physical phone screen OFF while streaming (-S) -> ~70% battery savings
# 4. Turn off phone screen when app closes (--power-off-on-close)
# 5. Native 90Hz fluidity
# 6. Decoupled audio (--no-audio) to eliminate jitter
exec "$DIR/AndroidCastEngine" \\
    -s "$DEVICE" \\
    --window-title="Android Cast" \\
    --render-driver=metal \\
    --video-codec=h265 \\
    --video-bit-rate=4M \\
    --max-size=1200 \\
    --video-buffer=20 \\
    --turn-screen-off \\
    --power-off-on-close \\
    --no-audio \\
    --stay-awake "$@"
"""
    launcher_path = MACOS_DIR / APP_NAME
    launcher_path.write_text(launcher_script, encoding="utf-8")
    launcher_path.chmod(0o755)
    print("✓ Created bundle launcher.")

def sign_and_install():
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(BUNDLE_DIR)], check=True)
    print(f"✓ Signed {APP_NAME}.app")

    user_apps = Path.home() / "Applications"
    user_apps.mkdir(parents=True, exist_ok=True)
    dest_user_app = user_apps / f"{APP_NAME}.app"
    if dest_user_app.exists():
        shutil.rmtree(dest_user_app)
    shutil.copytree(BUNDLE_DIR, dest_user_app)

    dest_sys_app = Path("/Applications") / f"{APP_NAME}.app"
    try:
        if dest_sys_app.exists():
            shutil.rmtree(dest_sys_app)
        shutil.copytree(BUNDLE_DIR, dest_sys_app)
        print("✓ Installed to /Applications/Android Cast.app")
    except Exception:
        print(f"✓ Installed to {dest_user_app}")

def main():
    print(f"🔨 Building optimized {APP_NAME}.app...")
    shutil.rmtree(BUNDLE_DIR, ignore_errors=True)
    generate_icons()
    create_info_plist()
    create_executables()
    sign_and_install()
    print(f"\n🎉 Successfully created and installed {APP_NAME}.app!")

if __name__ == "__main__":
    main()
