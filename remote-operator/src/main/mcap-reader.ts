import { McapStreamReader } from '@mcap/core'
import { readFile } from 'fs/promises'
import type { ControlState } from './types'

export interface McapFrame {
  jpeg: string // base64-encoded JPEG
  controls: ControlState
  timestampNs: number
}

export async function readMcapFile(filePath: string): Promise<McapFrame[]> {
  const fileData = await readFile(filePath)
  const reader = new McapStreamReader()
  reader.append(new Uint8Array(fileData))

  const channels = new Map<number, string>() // channelId -> topic
  const cameraFrames: { seq: number; jpeg: string; ts: number }[] = []
  const controlFrames: { seq: number; controls: ControlState; ts: number }[] = []

  for (;;) {
    const record = reader.nextRecord()
    if (!record) break

    if (record.type === 'Channel') {
      channels.set(record.id, record.topic)
    } else if (record.type === 'Message') {
      const topic = channels.get(record.channelId)
      if (topic === '/camera') {
        const base64 = Buffer.from(record.data).toString('base64')
        cameraFrames.push({
          seq: record.sequence,
          jpeg: base64,
          ts: Number(record.logTime)
        })
      } else if (topic === '/controls') {
        const json = new TextDecoder().decode(record.data)
        const ctrl = JSON.parse(json) as ControlState
        controlFrames.push({
          seq: record.sequence,
          controls: ctrl,
          ts: Number(record.logTime)
        })
      }
    }
  }

  // Pair 1:1 by index (they were written paired in the recorder)
  const count = Math.min(cameraFrames.length, controlFrames.length)
  const frames: McapFrame[] = []

  for (let i = 0; i < count; i++) {
    frames.push({
      jpeg: cameraFrames[i].jpeg,
      controls: controlFrames[i].controls,
      timestampNs: cameraFrames[i].ts
    })
  }

  return frames
}
