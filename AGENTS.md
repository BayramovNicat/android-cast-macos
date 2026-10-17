# AGENTS.md — Guidelines for AI Coding Assistants

This document provides architecture context, design decisions, and strict guidelines for AI agents working in this repository.

---

## 📱 Project Overview

**Android Cast** is a battery-optimized, high-performance tool for macOS to wirelessly mirror and control Android devices using:
- **scrcpy** with Apple Metal GPU VSync (`--render-driver=metal`)
- **Hardware H.265 / HEVC** video encoding
- **ADB over Wi-Fi** with automatic lock screen detection and unlocking

---

## ⚙️ Architecture & File Responsibilities

- **[`main.py`](main.py)**: CLI entrypoint, argument parsing (`--battery`, `--performance`, `--pin`, etc.), and interactive menu.
- **[`device.py`](device.py)**: ADB device discovery, lock detection (`dumpsys trust`), dynamic resolution calculation (`wm size`), and lockscreen unlock logic.
- **[`engine.py`](engine.py)**: Constructs optimized `scrcpy` arguments and manages the streaming subprocess.
- **[`config.py`](config.py)**: Streaming profile definitions (Battery Saver, Balanced, Ultra Performance) and `.env` loader.
- **[`build_app.py`](build_app.py)**: Generates high-res macOS `.icns` icons, bundles `Android Cast.app`, code-signs with ad-hoc identity, and installs to `/Applications`.
- **[`launcher.sh`](launcher.sh)**: Standalone shell script bundled into the application to launch scrcpy with auto-unlock.
- **[`cast.sh`](cast.sh)**: Shell wrapper to invoke `main.py` directly from the terminal.
- **[`.env`](.env) / [`.env.example`](.env.example)**: Stores local credentials (`ANDROID_PIN`). `.env` is git-ignored.

---

## 🚨 Strict Rules & Conventions

### 1. Python 3.9+ Compatibility
- macOS default Command Line Tools ship with **Python 3.9.6**.
- **Always include `from __future__ import annotations`** at the very top of every Python file so PEP 604 union types (`Path | None`, `int | None`) work on Python 3.9 without runtime errors.
- Do not introduce heavy external dependencies. The core mirroring logic should rely on Python standard library + `scrcpy` + `adb`.

### 2. Universal Android Support (No Hardcoded Models)
- **Never hardcode specific device models, brands, or screen resolutions.**
- For touch/swipe gestures, always determine screen resolution dynamically via `wm size` (as implemented in `device.py` and `build_app.py`), and use proportional coordinates (e.g. Center X, 75% height to 35% height).

### 3. No Hardcoded Personal Paths
- **Never hardcode absolute paths containing local usernames** (e.g., `/Users/username/...`).
- Always use relative paths (`Path(__file__).parent`, `$DIR`), `$HOME`, or `Path.home()`.

### 4. Security & Environment Variables
- Never commit actual passwords, PINs, or private IPs into source code or `.env.example`.
- All credentials must be read from `.env`, `~/.android_cast.env`, or environment variables (`ANDROID_PIN` / `ANDROID_PASSWORD`).

---

## 🛠️ Validation & Build Commands

Before concluding any task, verify your changes with these commands:

```bash
# 1. Verify Python syntax on system Python
npm run check
# or: python3 -m py_compile main.py config.py device.py engine.py build_app.py

# 2. Rebuild and install macOS app bundle if build_app.py was modified
npm run build
# or: python3 build_app.py

# 3. Verify launcher shell syntax
bash -n "/Applications/Android Cast.app/Contents/MacOS/Android Cast"
```
