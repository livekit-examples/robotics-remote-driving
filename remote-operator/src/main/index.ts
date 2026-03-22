import { app, BrowserWindow, shell, nativeImage } from 'electron'
import { join } from 'path'
import { registerIpcHandlers } from './ipc-handlers'

app.setName('LiveKit Driving')
const isDev = !app.isPackaged

function createWindow(): BrowserWindow {
  const icon = nativeImage.createFromPath(join(__dirname, '../../build/icon.png'))

  const win = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 960,
    minHeight: 640,
    backgroundColor: '#000000',
    icon,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true
    }
  })

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  if (isDev && process.env['ELECTRON_RENDERER_URL']) {
    win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'))
  }

  return win
}

app.whenReady().then(() => {
  const win = createWindow()
  registerIpcHandlers(win)

  app.on('activate', () => {
    // On macOS, re-create window but don't re-register IPC handlers (they're global)
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  app.quit()
})
