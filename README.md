# Pico Driving

Remote-control an RC car over LiveKit, record driving data, train a neural network, and let it drive autonomously.

## Quick Start

```sh
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and enter the project
git clone <repo-url> && cd robotics-driving-example

# Copy env template and fill in your LiveKit credentials
cp .env.example .env.local
```

### 1. Drive the car

**On the Raspberry Pi** (connected to Pico + camera):

```sh
uv run local-bridge
```

**On your laptop** — generate a token and open the GUI:

```sh
uv run token-creator
# Copy the URL and Token into the app

cd remote-operator
pnpm install && pnpm dev
```

Use WASD to drive, Tab for speed, Space for brake.

### 2. Record a dataset

In the remote-operator app, click **Record**, drive around, click **Stop**, and save the `.mcap` file. Repeat for multiple episodes.

### 3. Convert to LeRobot format

```sh
uv run python -m lerobot_training convert \
  --input episodes/*.mcap \
  --output ./dataset
```

### 4. Train a policy

```sh
uv run python -m lerobot_training train \
  --dataset ./dataset \
  --policy act \
  --steps 50000
```

### 5. Let it drive

```sh
uv run python -m lerobot_training infer \
  --checkpoint ./outputs/train/checkpoints/last/pretrained_model
```

### 6. Upload dataset to HuggingFace (optional)

```sh
uv run python -m lerobot_training upload \
  --dataset ./dataset \
  --repo-id yourname/rc-car-driving
```

---

## Architecture

```
[Laptop]                            [Raspberry Pi]                [Pico]
remote-operator/ (Electron)         local-bridge/                 pico-firmware/
  WASD → data channel ──────────→     data channel → serial ──→    GPIO → remote buttons
  video ← video track ←────────────    camera → video track
  record → .mcap files

remote-agent/ (AI voice)
  voice ↔ audio tracks ↔──────────     mic / speaker ↔ audio
  tools → data channel ──────────→

lerobot-training/
  .mcap → LeRobot dataset → train policy → infer over LiveKit
```

## Components

| Package | Description |
|---------|-------------|
| `remote-operator/` | Electron + React teleop GUI with MCAP recording and replay |
| `local-bridge/` | Raspberry Pi: streams camera, bridges LiveKit commands to Pico serial |
| `remote-agent/` | AI voice agent (Gemini Live) that drives via function tools |
| `remote-controller/` | Pygame keyboard controller (lightweight alternative to remote-operator) |
| `local-controller/` | Direct USB serial controller, no LiveKit needed |
| `token-creator/` | Generate LiveKit access tokens |
| `lerobot-training/` | MCAP conversion, policy training (ACT/Diffusion), LiveKit inference |
| `car-protocol/` | Shared library: button pin IDs, serial encoding, data channel commands |
| `pico-firmware/` | RP2040 firmware: serial → GPIO open-drain to simulate remote buttons |

All Python packages are runnable via `uv run <name> --help`.

## Hardware

- **Raspberry Pi Pico** (RP2040) — GPIO 16–21 wired to 6 buttons on the RC remote
- **Raspberry Pi** (any model with USB + camera) — runs local-bridge
- **USB cable** connecting Pi to Pico

## Setup

### Prerequisites

- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Node.js](https://nodejs.org/) — for remote-operator (Electron app)
- [PlatformIO](https://platformio.org/) — for Pico firmware
- [ffmpeg](https://ffmpeg.org/) — for video encoding during dataset conversion
- A [LiveKit](https://livekit.io/) server (Cloud or self-hosted)

### Flash the Pico

```sh
cd pico-firmware && pio run -t upload
```

### Configure LiveKit

```sh
cp .env.example .env.local
```

| Variable | Description |
|----------|-------------|
| `LIVEKIT_URL` | LiveKit server URL (`wss://...`) |
| `LIVEKIT_API_KEY` | API key |
| `LIVEKIT_API_SECRET` | API secret |
| `LIVEKIT_ROOM` | Room name (default: `pico-driving`) |

## Controls

| Key | Action |
|-----|--------|
| W | Forward |
| S | Backward |
| A | Left |
| D | Right |
| Tab | Speed boost |
| Space | Brake |
| Esc | Quit |

## CLI Reference

```sh
uv run token-creator                    # Generate a LiveKit token
uv run token-creator --agent car-agent  # Generate token + dispatch AI agent
uv run local-bridge                     # Start Pi bridge
uv run local-bridge --agent car-agent   # Start bridge + dispatch agent
uv run remote-controller                # Pygame controller
uv run remote-agent dev                 # AI voice agent
uv run local-controller                 # Direct USB control (no LiveKit)

# Dataset pipeline
uv run python -m lerobot_training convert  --input *.mcap --output ./dataset
uv run python -m lerobot_training train    --dataset ./dataset --policy act
uv run python -m lerobot_training infer    --checkpoint ./outputs/.../pretrained_model
uv run python -m lerobot_training upload   --dataset ./dataset --repo-id user/name
```
