# Pico Driving

Remote control system for an RC vehicle using a Raspberry Pi Pico as a signal spoof for a physical remote with active-low buttons. Supports direct USB control, low-latency remote driving over LiveKit with a live camera feed, and AI-powered autonomous driving via voice commands.

## Architecture

```
[Laptop / Cloud]                        [Raspberry Pi]                    [Pico]
remote-controller/                      local-bridge/                     pico-firmware/
  keyboard → data channel ──────────→     data channel → serial ──────→    GPIO open-drain
  pygame   ← video track  ←────────────    camera → video track            → remote buttons
                     (LiveKit Room)
remote-agent/
  AI voice ← video track  ←────────────
  tools   → data channel ──────────→
```

For local testing without LiveKit or a camera:

```
[Laptop]                    [Pico]
local-controller/           pico-firmware/
  keyboard → serial ────→    GPIO open-drain → remote buttons
```

## Components

| Directory | Runs on | Description |
|---|---|---|
| `car-protocol/` | (shared library) | Shared protocol constants and helpers — button pin IDs, serial encoding, LiveKit data channel command builders |
| `pico-firmware/` | Raspberry Pi Pico | Receives single-byte serial commands and drives 6 GPIO lines as open-drain outputs to simulate button presses on the physical remote |
| `local-bridge/` | Raspberry Pi | Connects to LiveKit, publishes camera video, receives control commands via data channel, and forwards them to the Pico over USB serial |
| `remote-controller/` | Laptop | Connects to LiveKit, displays the live camera stream, and sends keyboard commands over the data channel |
| `remote-agent/` | Laptop / Cloud | AI voice agent that sees through the car's camera and drives via function-calling tools, powered by Gemini Live |
| `local-controller/` | Laptop | Standalone controller that drives the Pico directly over USB serial with a pygame keyboard UI (no LiveKit or camera needed) |

## Project Structure

This is a [uv workspace](https://docs.astral.sh/uv/concepts/workspaces/) with a shared `car-protocol` library and four application packages:

```
car-protocol/car_protocol/      # Shared protocol (zero external deps)
    buttons.py                  #   Pin IDs, names, mappings
    serial.py                   #   Serial encoding + port detection
    commands.py                 #   LiveKit data channel command builders

local-controller/local_controller/
    main.py                     #   Pygame event loop + serial I/O
    ui.py                       #   Button status rendering

local-bridge/local_bridge/
    main.py                     #   Room connect + orchestration
    camera.py                   #   OpenCV capture → LiveKit video
    control.py                  #   Data channel → serial + keepalive

remote-controller/remote_controller/
    main.py                     #   Room connect + pygame event loop
    video.py                    #   LiveKit video stream receiver
    ui.py                       #   Overlay rendering

remote-agent/remote_agent/
    main.py                     #   AgentServer setup + entrypoint
    car_agent.py                #   CarAgent class with function tools
```

## Hardware

- **Raspberry Pi Pico** (RP2040) — GPIO 16–21 wired to 6 buttons on the RC remote
  - Pins configured as open-drain: `OUTPUT` = pull line low (press), `INPUT` = high-Z (release)
- **Raspberry Pi** (any model with USB + camera) — runs the local bridge
- **USB cable** connecting the Pi to the Pico

### GPIO Pin Mapping

| GPIO | Button |
|------|--------|
| 16   | UP     |
| 17   | DOWN   |
| 18   | LEFT   |
| 19   | RIGHT  |
| 20   | SPEED  |
| 21   | BRAKE  |

## Serial Protocol

Single-byte binary commands at 115200 baud:

| Byte | Meaning |
|------|---------|
| `0x00` | Release all buttons |
| `0x10`–`0x15` (bit 7 = 0) | Press button on GPIO pin (bits 0–6) |
| `0x90`–`0x95` (bit 7 = 1) | Release button on GPIO pin (bits 0–6) |

The Pico has a 500ms watchdog — if no command is received within 500ms, all buttons are released. The local bridge sends keepalive presses every 300ms to prevent this.

## Setup

### Prerequisites

- [uv](https://github.com/astral-sh/uv) — Python package manager
- [PlatformIO](https://platformio.org/) — for building and flashing the Pico firmware
- A LiveKit server (Cloud or self-hosted) — only needed for remote driving

### Flash the Pico

```sh
cd pico-firmware
pio run -t upload
```

Or copy the built `pico-firmware/.pio/build/pico/firmware.uf2` to the Pico in BOOTSEL mode.

### Configure LiveKit

```sh
cp .env.example .env.local
# Edit .env.local with your LiveKit credentials
```

| Variable | Description |
|---|---|
| `LIVEKIT_URL` | LiveKit server URL |
| `LIVEKIT_API_KEY` | API key |
| `LIVEKIT_API_SECRET` | API secret |
| `LIVEKIT_ROOM` | Room name (default: `pico-driving`) |

## Usage

### Remote Driving (over LiveKit)

**On the Raspberry Pi** — start the local bridge to stream the camera and bridge commands to the Pico:

```sh
cd local-bridge
uv sync
uv run python -m local_bridge
```

Set `SERIAL_PORT` env var to override auto-detection (default: `/dev/ttyACM*`).

**On your laptop** — start the controller to view the stream and drive:

```sh
cd remote-controller
uv sync
uv run python -m remote_controller
```

### AI Agent (over LiveKit)

Start the AI voice agent that sees through the car's camera and drives via voice commands:

```sh
cd remote-agent
uv sync
uv run python -m remote_agent dev
```

The agent uses Gemini Live for native audio/video understanding and exposes driving controls as function tools.

### Direct USB Control (no LiveKit)

Connect the Pico directly to your laptop and run:

```sh
cd local-controller
uv sync
uv run pico-controller
```

Pass a serial port as an argument to override auto-detection:

```sh
uv run pico-controller /dev/tty.usbmodem1234
```

### Controls

| Key   | Button |
|-------|--------|
| W     | UP     |
| S     | DOWN   |
| A     | LEFT   |
| D     | RIGHT  |
| Tab   | SPEED  |
| Space | BRAKE  |
| Esc   | Quit   |
