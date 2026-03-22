import { ipcMain, dialog, BrowserWindow } from 'electron'
import { writeFile } from 'fs/promises'
import { McapRecorder } from './mcap-recorder'
import { readMcapFile } from './mcap-reader'

export function registerIpcHandlers(win: BrowserWindow): void {
  const recorder = new McapRecorder()

  ipcMain.handle('recorder:start', async () => {
    await recorder.start()
  })

  ipcMain.on('recorder:frame', (_event, jpegBuffer: Uint8Array, controls) => {
    recorder.appendFrame(Buffer.from(jpegBuffer), controls)
  })

  ipcMain.handle('recorder:stop', async () => {
    const buffer = await recorder.stop()
    return buffer
  })

  ipcMain.handle('dialog:save', async (_event, data: Uint8Array) => {
    const { filePath } = await dialog.showSaveDialog(win, {
      defaultPath: `episode_${Date.now()}.mcap`,
      filters: [{ name: 'MCAP', extensions: ['mcap'] }]
    })
    if (filePath) {
      await writeFile(filePath, Buffer.from(data))
      return filePath
    }
    return null
  })

  // MCAP replay
  ipcMain.handle('mcap:open', async () => {
    const { filePaths } = await dialog.showOpenDialog(win, {
      filters: [{ name: 'MCAP', extensions: ['mcap'] }],
      properties: ['openFile']
    })
    if (filePaths.length === 0) return null
    return readMcapFile(filePaths[0])
  })

  ipcMain.handle('mcap:read', async (_event, filePath: string) => {
    return readMcapFile(filePath)
  })
}
