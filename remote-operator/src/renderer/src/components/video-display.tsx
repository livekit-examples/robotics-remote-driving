import { useEffect, useRef, useCallback } from 'react'
import type { RemoteTrack } from 'livekit-client'
import { Spinner } from './ui/spinner'
import type { ConnectionState, ControlState } from '../lib/constants'

const CAPTURE_INTERVAL = 33 // ms (~30fps)

export interface VideoMeta {
  width: number
  height: number
  fps: number
}

interface VideoDisplayProps {
  videoTrack: RemoteTrack | null
  connectionState: ConnectionState
  isRecording: boolean
  controls: ControlState
  onFrame: (videoEl: HTMLVideoElement, controls: ControlState) => void
  onMeta?: (meta: VideoMeta | null) => void
}

function Placeholder({ message }: { message: string }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-5 rounded-[3px] bg-white/5 flex items-center justify-center">
          <svg className="w-8 h-8 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
          </svg>
        </div>
        <p className="text-white/30 text-sm">{message}</p>
      </div>
    </div>
  )
}

function Loading({ message }: { message: string }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="text-center">
        <Spinner className="w-8 h-8 mx-auto mb-3" />
        <p className="text-white/30 text-sm">{message}</p>
      </div>
    </div>
  )
}

export function VideoDisplay({ videoTrack, connectionState, isRecording, controls, onFrame, onMeta }: VideoDisplayProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const rafRef = useRef(0)
  const lastCapture = useRef(0)

  // Keep mutable refs for values read inside rAF / timers
  const controlsRef = useRef(controls)
  controlsRef.current = controls
  const onMetaRef = useRef(onMeta)
  onMetaRef.current = onMeta

  // --- Video track attach + metadata polling ---
  useEffect(() => {
    const videoEl = videoRef.current
    if (!videoEl || !videoTrack) {
      onMetaRef.current?.(null)
      return
    }

    const mediaEl = videoTrack.attach(videoEl)
    let prevDecoded = 0
    let prevTime = performance.now()

    const metaTimer = setInterval(() => {
      const stream = mediaEl.srcObject
      const settings = stream instanceof MediaStream
        ? stream.getVideoTracks()[0]?.getSettings()
        : null

      const now = performance.now()
      const decoded = (videoEl as unknown as Record<string, number>).webkitDecodedFrameCount
      let fps = settings?.frameRate ?? 0
      if (decoded !== undefined) {
        const dt = (now - prevTime) / 1000
        if (dt > 0) fps = Math.round((decoded - prevDecoded) / dt)
        prevDecoded = decoded
        prevTime = now
      }

      onMetaRef.current?.({ width: videoEl.videoWidth, height: videoEl.videoHeight, fps: Math.round(fps) })
    }, 1000)

    return () => {
      clearInterval(metaTimer)
      videoTrack.detach(mediaEl)
      onMetaRef.current?.(null)
    }
  }, [videoTrack])

  // --- Recording capture loop ---
  const captureLoop = useCallback(() => {
    const videoEl = videoRef.current
    if (!videoEl || !isRecording) return

    const now = performance.now()
    if (now - lastCapture.current >= CAPTURE_INTERVAL) {
      lastCapture.current = now
      onFrame(videoEl, controlsRef.current)
    }

    rafRef.current = requestAnimationFrame(captureLoop)
  }, [isRecording, onFrame])

  useEffect(() => {
    if (!isRecording) return
    lastCapture.current = 0
    rafRef.current = requestAnimationFrame(captureLoop)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [isRecording, captureLoop])

  // --- Render ---
  if (connectionState === 'disconnected') return <Placeholder message="Enter token to connect" />
  if (connectionState === 'connecting' || !videoTrack) {
    return <Loading message={connectionState === 'connecting' ? 'Connecting...' : 'Waiting for video...'} />
  }

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      muted
      className="absolute inset-0 w-full h-full object-cover bg-black"
    />
  )
}
