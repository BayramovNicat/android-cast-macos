#!/usr/bin/env python3
from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
from pathlib import Path

APP_NAME = "Android Cast"
REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
BUNDLE_DIR = REPO_ROOT / f"{APP_NAME}.app"
CONTENTS_DIR = BUNDLE_DIR / "Contents"
MACOS_DIR = CONTENTS_DIR / "MacOS"
RESOURCES_DIR = CONTENTS_DIR / "Resources"

def copy_assets():
    """Copy high-resolution macOS ICNS and PNG assets into the bundle."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    for asset_name in ["AppIcon.icns", "scrcpy.png", "disconnected.png"]:
        src = ASSETS_DIR / asset_name
        if src.is_file():
            shutil.copy2(src, RESOURCES_DIR / asset_name)
    print("✓ Copied application icon and asset resources.")

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
    env_source = REPO_ROOT / ".env"
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
    copy_assets()
    create_info_plist()
    create_executables()
    sign_and_install()
    print(f"\n🎉 Successfully created and installed {APP_NAME}.app!")

if __name__ == "__main__":
    main()
