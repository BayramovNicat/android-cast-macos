#!/usr/bin/env python3
from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import tempfile
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
    with tempfile.TemporaryDirectory(suffix=".iconset", prefix="AndroidCast_") as temp_dir:
        iconset_dir = Path(temp_dir)

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
    print("✓ Created custom high-res AppIcon.icns.")

def create_info_plist():
    """Generate macOS Info.plist using Python's standard plistlib."""
    info_dict = {
        "CFBundleExecutable": APP_NAME,
        "CFBundleIconFile": "AppIcon",
        "CFBundleIdentifier": "com.user.androidcast",
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "2.0",
        "CFBundleVersion": "2.0",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    }
    plist_path = CONTENTS_DIR / "Info.plist"
    with open(plist_path, "wb") as f:
        plistlib.dump(info_dict, f)
    print("✓ Created Info.plist.")

def find_scrcpy_binary() -> str:
    """Locate scrcpy executable on Apple Silicon or Intel Macs."""
    found = shutil.which("scrcpy")
    if found:
        return found
    for p in ["/opt/homebrew/bin/scrcpy", "/usr/local/bin/scrcpy"]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    raise FileNotFoundError("scrcpy binary not found. Please install via: brew install scrcpy")

def find_scrcpy_server() -> str | None:
    """Locate scrcpy-server jar on Apple Silicon or Intel Macs."""
    candidates = [
        "/opt/homebrew/share/scrcpy/scrcpy-server",
        "/usr/local/share/scrcpy/scrcpy-server",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

def create_executables():
    MACOS_DIR.mkdir(parents=True, exist_ok=True)

    # Embed .env into App Resources and copy to ~/.android_cast.env for portability
    env_source = Path(__file__).parent / ".env"
    if env_source.is_file():
        shutil.copy2(env_source, RESOURCES_DIR / ".env")
        shutil.copy2(env_source, Path.home() / ".android_cast.env")

    # Embed scrcpy-server into Resources if present
    server_path = find_scrcpy_server()
    if server_path:
        shutil.copy2(server_path, RESOURCES_DIR / "scrcpy-server")

    scrcpy_source = find_scrcpy_binary()
    engine_dest = MACOS_DIR / "AndroidCastEngine"
    shutil.copy2(scrcpy_source, engine_dest)
    engine_dest.chmod(0o755)

    # Copy standalone launcher script into bundle
    launcher_src = Path(__file__).parent / "launcher.sh"
    launcher_dest = MACOS_DIR / APP_NAME
    shutil.copy2(launcher_src, launcher_dest)
    launcher_dest.chmod(0o755)
    print("✓ Installed bundle launcher from launcher.sh.")

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
