import { useState, useCallback, useRef, useEffect } from 'react'

export interface RecorderState {
  isRecording: boolean
  frameCount: number
  elapsed: number
  startRecording: () => Promise<void>
  stopRecording: () => Promise<void>
  captureFrame: (videoEl: HTMLVideoElement) => void
}

export function useRecorder(): RecorderState {
  const [isRecording, setIsRecording] = useState(false)
  const [frameCount, setFrameCount] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const frameCountRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startTimeRef = useRef(0)

  useEffect(() => {
    canvasRef.current = document.createElement('canvas')
  }, [])

  const captureFrame = useCallback((videoEl: HTMLVideoElement) => {
    const canvas = canvasRef.current
    if (!canvas || !videoEl.videoWidth) return

    canvas.width = videoEl.videoWidth
    canvas.height = videoEl.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.drawImage(videoEl, 0, 0)
    canvas.toBlob(
      (blob) => {
        if (blob) {
          blob.arrayBuffer().then((buf) => {
            window.electronAPI.sendFrame(new Uint8Array(buf))
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
    setIsRecording(true)

    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
  }, [])

  const stopRecording = useCallback(async () => {
    setIsRecording(false)
    if (timerRef.current) clearInterval(timerRef.current)

    const mcapData = await window.electronAPI.stopRecording()
    await window.electronAPI.saveFile(mcapData)
  }, [])

  return { isRecording, frameCount, elapsed, startRecording, stopRecording, captureFrame }
}
