import { useEffect, useRef, useCallback } from 'react'
import type { RemoteTrack } from 'livekit-client'
import { Spinner } from './ui/spinner'
import type { ConnectionState } from '../lib/constants'

interface VideoDisplayProps {
  videoTrack: RemoteTrack | null
  connectionState: ConnectionState
  isRecording: boolean
  onFrame: (videoEl: HTMLVideoElement) => void
}

export function VideoDisplay({ videoTrack, connectionState, isRecording, onFrame }: VideoDisplayProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const frameLoopRef = useRef<number>(0)
  const lastCaptureRef = useRef<number>(0)

  // Attach/detach video track
  useEffect(() => {
    const videoEl = videoRef.current
    if (!videoEl || !videoTrack) return

    const mediaEl = videoTrack.attach(videoEl)
    return () => { videoTrack.detach(mediaEl) }
  }, [videoTrack])

  // Frame capture loop for recording (~10fps)
  const captureLoop = useCallback(() => {
    const videoEl = videoRef.current
    if (!videoEl || !isRecording) return

    const now = performance.now()
    if (now - lastCaptureRef.current >= 100) {
      lastCaptureRef.current = now
      onFrame(videoEl)
    }

    frameLoopRef.current = requestAnimationFrame(captureLoop)
  }, [isRecording, onFrame])

  useEffect(() => {
    if (isRecording) {
      lastCaptureRef.current = 0
      frameLoopRef.current = requestAnimationFrame(captureLoop)
    }
    return () => {
      if (frameLoopRef.current) cancelAnimationFrame(frameLoopRef.current)
    }
  }, [isRecording, captureLoop])

  if (connectionState === 'disconnected') {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-5 rounded-[3px] bg-white/5 flex items-center justify-center">
            <svg className="w-8 h-8 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
            </svg>
          </div>
          <p className="text-white/30 text-sm">Enter token to connect</p>
        </div>
      </div>
    )
  }

  if (connectionState === 'connecting' || !videoTrack) {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <Spinner className="w-8 h-8 mx-auto mb-3" />
          <p className="text-white/30 text-sm">
            {connectionState === 'connecting' ? 'Connecting...' : 'Waiting for video...'}
          </p>
        </div>
      </div>
    )
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
