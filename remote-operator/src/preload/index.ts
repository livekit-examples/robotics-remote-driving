import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  // Recording
  startRecording: () => ipcRenderer.invoke('recorder:start'),
  stopRecording: () => ipcRenderer.invoke('recorder:stop'),
  sendFrame: (jpeg: Uint8Array, controls: unknown) => ipcRenderer.send('recorder:frame', jpeg, controls),
  saveFile: (buffer: Uint8Array) => ipcRenderer.invoke('dialog:save', buffer),

  // Replay
  openMcap: () => ipcRenderer.invoke('mcap:open'),
  readMcap: (filePath: string) => ipcRenderer.invoke('mcap:read', filePath)
})
