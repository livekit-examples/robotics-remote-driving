export interface ControlState {
  w: boolean
  a: boolean
  s: boolean
  d: boolean
  speed: boolean
  brake: boolean
}

export interface McapFrame {
  jpeg: string // base64-encoded JPEG
  controls: ControlState
  timestampNs: number
}

export interface ElectronAPI {
  startRecording: () => Promise<void>
  stopRecording: () => Promise<Uint8Array>
  sendFrame: (jpeg: Uint8Array, controls: ControlState) => void
  saveFile: (buffer: Uint8Array) => Promise<string | null>

  // Replay
  openMcap: () => Promise<McapFrame[] | null>
  readMcap: (filePath: string) => Promise<McapFrame[]>
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}
