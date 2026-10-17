#!/usr/bin/env bash
# ==============================================================================
# Android Cast - macOS Application Launcher
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$DIR/../Resources"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export SCRCPY_ICON_DIR="$RESOURCES_DIR"

# Locate scrcpy-server jar
if [ -f "$RESOURCES_DIR/scrcpy-server" ]; then
    export SCRCPY_SERVER_PATH="$RESOURCES_DIR/scrcpy-server"
elif [ -f "/opt/homebrew/share/scrcpy/scrcpy-server" ]; then
    export SCRCPY_SERVER_PATH="/opt/homebrew/share/scrcpy/scrcpy-server"
elif [ -f "/usr/local/share/scrcpy/scrcpy-server" ]; then
    export SCRCPY_SERVER_PATH="/usr/local/share/scrcpy/scrcpy-server"
fi

get_device() {
    adb devices | grep -E '(\bdevice\b)' | grep -v 'List of' | head -n 1 | awk '{print $1}'
}

DEVICE=$(get_device)

# Retry auto-discovery if needed
if [ -z "$DEVICE" ]; then
    sleep 1.5
    DEVICE=$(get_device)
fi

# Fallback alert with prompt if device is offline
if [ -z "$DEVICE" ]; then
    USER_ACTION=$(osascript -e '
        set dialogResult to display dialog "No Android phone detected over Wi-Fi.\n\nMake sure your Android phone is on Wi-Fi with Wireless Debugging enabled." buttons {"Cancel", "Enter IP...", "Retry"} default button "Retry" with title "Android Cast" with icon note
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
            set ipInput to display dialog "Enter your phone Wireless Debugging IP & Port:\n(e.g. 192.168.0.3:40957)" default answer "192.168.0.3:40957" buttons {"Cancel", "Connect"} default button "Connect" with title "Android Cast"
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

# Locate .env configuration file
ENV_FILE="$RESOURCES_DIR/.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$HOME/.android_cast.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$DIR/../../../../.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE="$HOME/.env"

ANDROID_PIN=""
if [ -f "$ENV_FILE" ]; then
    ANDROID_PIN=$(grep -E '^(ANDROID_PIN|ANDROID_PASSWORD)=' "$ENV_FILE" | head -n 1 | cut -d'=' -f2- | tr -d ' "\r\t')
fi

# Auto-unlock if device is locked
IS_LOCKED=$(adb -s "$DEVICE" shell dumpsys trust 2>/dev/null | grep -E "deviceLocked=1|deviceLocked=true")
if [ -n "$IS_LOCKED" ] && [ -n "$ANDROID_PIN" ]; then
    # Dynamic swipe coordinates for any Android screen resolution
    SIZE=$(adb -s "$DEVICE" shell wm size 2>/dev/null | grep -oE '[0-9]+x[0-9]+' | head -n 1)
    WIDTH="${SIZE%x*}"
    HEIGHT="${SIZE#*x}"
    [ -z "$WIDTH" ] && WIDTH=1080
    [ -z "$HEIGHT" ] && HEIGHT=2400
    SWIPE_X=$((WIDTH / 2))
    SWIPE_Y1=$((HEIGHT * 3 / 4))
    SWIPE_Y2=$((HEIGHT / 3))

    adb -s "$DEVICE" shell "input keyevent 224 && sleep 0.7 && input swipe $SWIPE_X $SWIPE_Y1 $SWIPE_X $SWIPE_Y2 250 && sleep 0.7 && input text \"$ANDROID_PIN\" && sleep 0.2 && input keyevent 66"
    sleep 0.4
fi

# High-Efficiency scrcpy Execution:
# 1. Hardware Metal VSync presentation
# 2. Hardware H.265 encoder
# 3. Physical phone screen OFF while streaming (-S) -> ~70% battery savings
# 4. Turn off phone screen when app closes (--power-off-on-close)
# 5. Native 90Hz fluidity
# 6. Decoupled audio (--no-audio) to eliminate jitter
exec "$DIR/AndroidCastEngine" \
    -s "$DEVICE" \
    --window-title="Android Cast" \
    --render-driver=metal \
    --video-codec=h265 \
    --video-bit-rate=4M \
    --max-size=1200 \
    --video-buffer=20 \
    --turn-screen-off \
    --power-off-on-close \
    --no-audio \
    --stay-awake "$@"
