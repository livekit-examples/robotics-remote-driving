# Remote Operator

Electron teleop GUI for driving the robot and recording datasets.

## Setup

```sh
cd remote-operator
npm install
npm run dev
```

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
