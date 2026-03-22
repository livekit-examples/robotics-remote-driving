# Remote Operator

Electron teleop GUI for driving the robot and recording datasets.

## Prerequisites

You need **Node.js** (v18+) and **pnpm** installed.

### Install Node.js

**macOS** (via Homebrew):

```sh
brew install node
```

**Linux** (via NodeSource):

```sh
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows**: Download the installer from https://nodejs.org

### Install pnpm

```sh
npm install -g pnpm
```

### Electron system dependencies (Linux only)

Electron requires some system libraries on Linux:

```sh
# Debian/Ubuntu
sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libxss1 libasound2
```

macOS and Windows need no extra system dependencies — Electron bundles everything.

## Setup

```sh
cd remote-operator
pnpm install
pnpm dev
```

This starts the Electron app in development mode with hot reload.

### Build & package

To create a distributable app (`.dmg` on macOS, `.exe` on Windows, `.AppImage` on Linux):

```sh
pnpm package
```

The installer will be in `remote-operator/dist/`. Send the file to your friend — no Node.js or dev tools needed on their machine.

## Usage

1. Generate a token: `uv run token-creator` (from the project root)
2. Paste the **URL** and **Token** into the connect bar
3. Click **Connect** — you should see the camera feed
4. Drive with WASD, Tab (speed), Space (brake)
5. Click **Record** to capture an episode, **Stop** to save as `.mcap`

## Replay

Switch to the **Replay** tab, drop a `.mcap` file (or click to open), and scrub through the recording. The key overlay shows exactly what was pressed at each frame.

Keyboard shortcuts: Space (play/pause), Left/Right arrows (step frame), Escape (close).

## Tech Stack

- Electron + React + TypeScript
- Tailwind CSS + shadcn/ui
- LiveKit (`livekit-client`) for WebRTC video + data channel
- MCAP (`@mcap/core`) for dataset recording
