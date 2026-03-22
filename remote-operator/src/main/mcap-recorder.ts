import { McapWriter, IWritable } from '@mcap/core'
import { open, FileHandle, unlink, readFile } from 'fs/promises'
import { tmpdir } from 'os'
import { join } from 'path'
import { type ControlState } from './types'

// --- File-backed writable for McapWriter ---

class FileHandleWritable implements IWritable {
  private handle: FileHandle
  private _position = 0n

  constructor(handle: FileHandle) {
    this.handle = handle
  }

  position(): bigint {
    return this._position
  }

  async write(buffer: Uint8Array): Promise<void> {
    const { bytesWritten } = await this.handle.write(buffer, 0, buffer.length, Number(this._position))
    this._position += BigInt(bytesWritten)
  }
}

// --- MCAP schema/channel setup ---

const CONTROLS_SCHEMA = JSON.stringify({
  type: 'object',
  properties: {
    w: { type: 'boolean' },
    a: { type: 'boolean' },
    s: { type: 'boolean' },
    d: { type: 'boolean' },
    speed: { type: 'boolean' },
    brake: { type: 'boolean' },
  },
})

async function registerChannels(writer: McapWriter) {
  const cameraSchema = await writer.registerSchema({
    name: 'jpeg_frame',
    encoding: 'raw',
    data: new Uint8Array(0),
  })
  const controlsSchema = await writer.registerSchema({
    name: 'control_state',
    encoding: 'jsonschema',
    data: new TextEncoder().encode(CONTROLS_SCHEMA),
  })

  const camera = await writer.registerChannel({
    topic: '/camera',
    schemaId: cameraSchema,
    messageEncoding: 'raw',
    metadata: new Map(),
  })
  const controls = await writer.registerChannel({
    topic: '/controls',
    schemaId: controlsSchema,
    messageEncoding: 'json',
    metadata: new Map(),
  })

  return { camera, controls }
}

// --- Recorder ---

export class McapRecorder {
  private writer: McapWriter | null = null
  private fileHandle: FileHandle | null = null
  private tempPath = ''
  private channelIds = { camera: 0, controls: 0 }
  private startTime = 0n
  private _frameCount = 0
  private writeQueue: Promise<void> = Promise.resolve()

  get frameCount() { return this._frameCount }
  get isRecording() { return this.writer !== null }

  async start(): Promise<void> {
    this.tempPath = join(tmpdir(), `recording_${Date.now()}.mcap`)
    this.fileHandle = await open(this.tempPath, 'w')

    this.writer = new McapWriter({
      writable: new FileHandleWritable(this.fileHandle),
      useStatistics: true,
      useChunks: true,
    })
    await this.writer.start({ library: 'remote-operator', profile: '' })
    this.channelIds = await registerChannels(this.writer)

    this._frameCount = 0
    this.writeQueue = Promise.resolve()
    this.startTime = process.hrtime.bigint()
  }

  appendFrame(jpegBuffer: Buffer, controls: ControlState): void {
    if (!this.writer) return

    const seq = this._frameCount
    const ts = process.hrtime.bigint() - this.startTime
    const jpeg = new Uint8Array(jpegBuffer)
    const ctrl = new TextEncoder().encode(JSON.stringify(controls))

    this.writeQueue = this.writeQueue
      .then(async () => {
        if (!this.writer) return
        await this.writer.addMessage({
          channelId: this.channelIds.camera,
          sequence: seq, logTime: ts, publishTime: ts,
          data: jpeg,
        })
        await this.writer.addMessage({
          channelId: this.channelIds.controls,
          sequence: seq, logTime: ts, publishTime: ts,
          data: ctrl,
        })
      })
      .catch(() => {}) // prevent one failed write from killing the chain

    this._frameCount++
  }

  async stop(): Promise<Uint8Array> {
    if (!this.writer || !this.fileHandle) throw new Error('Not recording')

    await this.writeQueue
    await this.writer.end()
    await this.fileHandle.close()

    const buffer = await readFile(this.tempPath)
    await unlink(this.tempPath).catch(() => {})

    this.writer = null
    this.fileHandle = null
    return new Uint8Array(buffer)
  }
}
