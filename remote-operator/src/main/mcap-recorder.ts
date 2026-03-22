import { McapWriter, IWritable } from '@mcap/core'
import { open, FileHandle, unlink, readFile } from 'fs/promises'
import { tmpdir } from 'os'
import { join } from 'path'
import { type ControlState } from './types'

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

export class McapRecorder {
  private writer: McapWriter | null = null
  private fileHandle: FileHandle | null = null
  private tempPath: string = ''
  private cameraChannelId = 0
  private controlsChannelId = 0
  private startTime: bigint = 0n
  private _frameCount = 0
  private writeQueue: Promise<void> = Promise.resolve()

  get frameCount(): number {
    return this._frameCount
  }

  get isRecording(): boolean {
    return this.writer !== null
  }

  async start(): Promise<void> {
    this.tempPath = join(tmpdir(), `recording_${Date.now()}.mcap`)
    this.fileHandle = await open(this.tempPath, 'w')
    const writable = new FileHandleWritable(this.fileHandle)

    this.writer = new McapWriter({ writable, useStatistics: true, useChunks: true })
    await this.writer.start({ library: 'remote-operator', profile: '' })

    const cameraSchemaId = await this.writer.registerSchema({
      name: 'jpeg_frame',
      encoding: 'raw',
      data: new Uint8Array(0)
    })

    const controlsSchemaData = JSON.stringify({
      type: 'object',
      properties: {
        w: { type: 'boolean' },
        a: { type: 'boolean' },
        s: { type: 'boolean' },
        d: { type: 'boolean' },
        speed: { type: 'boolean' },
        brake: { type: 'boolean' }
      }
    })

    const controlsSchemaId = await this.writer.registerSchema({
      name: 'control_state',
      encoding: 'jsonschema',
      data: new TextEncoder().encode(controlsSchemaData)
    })

    this.cameraChannelId = await this.writer.registerChannel({
      topic: '/camera',
      schemaId: cameraSchemaId,
      messageEncoding: 'raw',
      metadata: new Map()
    })

    this.controlsChannelId = await this.writer.registerChannel({
      topic: '/controls',
      schemaId: controlsSchemaId,
      messageEncoding: 'json',
      metadata: new Map()
    })

    this._frameCount = 0
    this.writeQueue = Promise.resolve()
    this.startTime = process.hrtime.bigint()
  }

  appendFrame(jpegBuffer: Buffer, controls: ControlState): void {
    if (!this.writer) return

    const seq = this._frameCount
    const now = process.hrtime.bigint() - this.startTime
    const cameraData = new Uint8Array(jpegBuffer)
    const controlData = new TextEncoder().encode(JSON.stringify(controls))

    this.writeQueue = this.writeQueue.then(async () => {
      if (!this.writer) return
      await this.writer.addMessage({
        channelId: this.cameraChannelId,
        sequence: seq,
        logTime: now,
        publishTime: now,
        data: cameraData
      })
      await this.writer.addMessage({
        channelId: this.controlsChannelId,
        sequence: seq,
        logTime: now,
        publishTime: now,
        data: controlData
      })
    })

    this._frameCount++
  }

  async stop(): Promise<Uint8Array> {
    if (!this.writer || !this.fileHandle) {
      throw new Error('Not recording')
    }

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
