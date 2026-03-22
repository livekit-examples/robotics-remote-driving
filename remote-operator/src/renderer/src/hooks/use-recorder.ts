import { useState, useCallback, useRef } from 'react'
import type { ControlState } from '../lib/constants'

const JPEG_QUALITY = 0.85
const UI_UPDATE_INTERVAL = 250 // ms — throttle React re-renders for counters
const DRAIN_TIMEOUT = 200 // ms — wait for in-flight toBlob callbacks before stop

export interface RecorderState {
  isRecording: boolean
  frameCount: number
  elapsed: number
  startRecording: () => Promise<void>
  stopRecording: () => Promise<void>
  captureFrame: (videoEl: HTMLVideoElement, controls: ControlState) => void
}

export function useRecorder(): RecorderState {
  const [isRecording, setIsRecording] = useState(false)
  const [frameCount, setFrameCount] = useState(0)
  const [elapsed, setElapsed] = useState(0)

  const canvas = useRef(document.createElement('canvas'))
  const ctx = useRef<CanvasRenderingContext2D | null>(null)
  const frames = useRef(0)
  const recording = useRef(false)
  const pending = useRef(false)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)
  const startedAt = useRef(0)

  const captureFrame = useCallback((videoEl: HTMLVideoElement, controls: ControlState) => {
    if (!videoEl.videoWidth || !recording.current || pending.current) return

    // Resize canvas only when video resolution changes
    const c = canvas.current
    if (c.width !== videoEl.videoWidth || c.height !== videoEl.videoHeight) {
      c.width = videoEl.videoWidth
      c.height = videoEl.videoHeight
      ctx.current = null
    }
    ctx.current ??= c.getContext('2d')
    if (!ctx.current) return

    // Snapshot controls + frame at the same instant
    const snap = { ...controls }
    pending.current = true

    ctx.current.drawImage(videoEl, 0, 0)
    c.toBlob(
      (blob) => {
        if (!blob || !recording.current) {
          pending.current = false
          return
        }
        blob.arrayBuffer().then((buf) => {
          pending.current = false
          if (!recording.current) return
          window.electronAPI.sendFrame(new Uint8Array(buf), snap)
          frames.current++
        })
      },
      'image/jpeg',
      JPEG_QUALITY,
    )
  }, [])

  const startRecording = useCallback(async () => {
    await window.electronAPI.startRecording()

    frames.current = 0
    pending.current = false
    startedAt.current = Date.now()
    recording.current = true

    setFrameCount(0)
    setElapsed(0)
    setIsRecording(true)

    timer.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt.current) / 1000))
      setFrameCount(frames.current)
    }, UI_UPDATE_INTERVAL)
  }, [])

  const stopRecording = useCallback(async () => {
    recording.current = false
    setIsRecording(false)
    if (timer.current) clearInterval(timer.current)

    await new Promise((r) => setTimeout(r, DRAIN_TIMEOUT))

    const mcapData = await window.electronAPI.stopRecording()
    await window.electronAPI.saveFile(mcapData)
  }, [])

  return { isRecording, frameCount, elapsed, startRecording, stopRecording, captureFrame }
}
