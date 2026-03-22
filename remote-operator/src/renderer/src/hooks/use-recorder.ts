import { useState, useCallback, useRef } from 'react'
import type { ControlState } from '../lib/constants'

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
  const canvasRef = useRef(document.createElement('canvas'))
  const frameCountRef = useRef(0)
  const recordingRef = useRef(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startTimeRef = useRef(0)

  const captureFrame = useCallback((videoEl: HTMLVideoElement, controls: ControlState) => {
    const canvas = canvasRef.current
    if (!canvas || !videoEl.videoWidth || !recordingRef.current) return

    canvas.width = videoEl.videoWidth
    canvas.height = videoEl.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Snapshot controls at the same instant as drawImage
    const snapshotControls = { ...controls }

    ctx.drawImage(videoEl, 0, 0)
    canvas.toBlob(
      (blob) => {
        if (blob && recordingRef.current) {
          blob.arrayBuffer().then((buf) => {
            if (!recordingRef.current) return
            window.electronAPI.sendFrame(new Uint8Array(buf), snapshotControls)
            frameCountRef.current++
            setFrameCount(frameCountRef.current)
          })
        }
      },
      'image/jpeg',
      0.85
    )
  }, [])

  const startRecording = useCallback(async () => {
    await window.electronAPI.startRecording()
    frameCountRef.current = 0
    setFrameCount(0)
    setElapsed(0)
    startTimeRef.current = Date.now()
    recordingRef.current = true
    setIsRecording(true)

    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
  }, [])

  const stopRecording = useCallback(async () => {
    recordingRef.current = false
    setIsRecording(false)
    if (timerRef.current) clearInterval(timerRef.current)

    // Wait for any in-flight toBlob/arrayBuffer callbacks to settle
    await new Promise((r) => setTimeout(r, 200))

    const mcapData = await window.electronAPI.stopRecording()
    await window.electronAPI.saveFile(mcapData)
  }, [])

  return { isRecording, frameCount, elapsed, startRecording, stopRecording, captureFrame }
}
