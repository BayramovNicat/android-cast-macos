# 📱 Android Cast (macOS)

A high-performance, battery-optimized tool to mirror and control your Android phone on macOS **100% over Wi-Fi** using Apple Metal GPU rendering.

---

## ✨ Highlights & Battery Optimizations

- **🔋 Up to ~75% Phone Battery Savings**:
  - Automatically turns the physical phone screen **OFF** while mirroring (`--turn-screen-off`).
  - Automatically puts the phone display back to sleep when the Mac window closes (`--power-off-on-close`).
- **🔓 Auto-Unlock on Launch (No Black Screen)**:
  - Automatically detects when your phone is locked (`dumpsys trust`).
  - Swipes up and enters your PIN from `.env` via ADB, completely bypassing Android's `FLAG_SECURE` black screen.
- **⚡ Silky Smooth Metal VSync**:
  - Uses Apple Metal hardware pipeline (`--render-driver=metal`) to eliminate screen tearing and minimize Mac GPU draw.
  - Fluid high refresh rate display matching (up to 90/120 Hz).
- **🚀 Hardware H.265 / HEVC**:
  - Encoded directly by your phone's hardware chip at an optimized 2.5–4 Mbps bitrate.
- **🎧 Jitter-Free Audio Decoupling**:
  - Audio sync packet queueing is disabled by default, preventing video freezes when your phone loads web pages.

---

## 🛠️ Prerequisites

Ensure you have `scrcpy` and Android platform tools installed on your Mac:

```bash
brew install scrcpy android-platform-tools
```

On your Android phone:
1. Go to **Settings** > **Developer options**.
2. Turn **ON** **Wireless debugging**.
3. Make sure your phone and Mac are connected to the same Wi-Fi network.

---

## ⚙️ Initial Setup

1. **Configure Lock Screen PIN**:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set your PIN or password:
   ```env
   ANDROID_PIN=your_pin_here
   ```

2. **Build and Install macOS App**:
   ```bash
   python3 build_app.py
   ```
   This generates and installs `Android Cast.app` directly into `/Applications`.

---

## 🚀 Usage

### 1. From macOS Spotlight / Launchpad (Easiest)
Open **Android Cast** (`Cmd + Space` &rarr; `Android Cast`). The app automatically discovers your phone over Wi-Fi, unlocks it if needed, and starts mirroring.

### 2. From Terminal
```bash
./cast.sh               # Interactive Menu
./cast.sh --battery     # Maximum Battery Saver mode (60 FPS, 2.5 Mbps)
./cast.sh --performance # Ultra Performance mode (90 Hz, screen stays on)
./cast.sh --view-only   # Read-only presentation mode (clicks disabled)
./cast.sh --pin 1234    # Override PIN to unlock
./cast.sh --no-unlock   # Skip auto-unlocking
./cast.sh --ip 192.168.0.3:40957 # Connect to specific IP:Port
```

### 3. Using NPM Scripts (Optional)
If you prefer using `npm` commands:
```bash
npm run build            # Build & install macOS app bundle to /Applications
npm start                # Launch interactive menu
npm run cast:battery     # Launch Battery Saver mode
npm run cast:performance # Launch Ultra Performance mode
npm run devices          # List connected ADB devices
npm run check            # Verify Python syntax
```

---

## ⌨️ Helpful Shortcuts While Mirroring

| Shortcut | Action |
| :--- | :--- |
| `Alt/Cmd + p` | Toggle phone power (Screen On / Off) |
| `Alt/Cmd + o` | Turn phone physical screen OFF (keep mirroring) |
| `Alt/Cmd + Shift + o` | Turn phone physical screen ON |
| `Alt/Cmd + b` / `Right-click` | Android Back button |
| `Alt/Cmd + h` / `Middle-click` | Android Home button |
| `Alt/Cmd + s` | Android App Switcher (Recent Apps) |
| `Alt/Cmd + f` | Toggle Fullscreen |
| `Alt/Cmd + q` | Quit Android Cast |

---

## 📁 Project Architecture

- **[`main.py`](main.py)** - CLI entrypoint and interactive mode selection.
- **[`device.py`](device.py)** - Wireless device discovery, lock detection, and ADB unlock logic.
- **[`engine.py`](engine.py)** - Constructs optimized `scrcpy` arguments and manages the streaming process.
- **[`config.py`](config.py)** - Streaming profiles (Battery, Balanced, Performance) and `.env` loader.
- **[`build_app.py`](build_app.py)** - Automates bundling, icon generation, code-signing, and installation to `/Applications`.
- **[`launcher.sh`](launcher.sh)** - Standalone shell launcher bundled into `Android Cast.app`.
- **[`cast.sh`](cast.sh)** - Convenient terminal wrapper for `./main.py`.
- **[`.env`](.env) / [`.env.example`](.env.example)** - Local configuration for your Android credentials.
