import { useState, useCallback, useRef, useEffect } from 'react'
import {
  Room,
  RoomEvent,
  Track,
  RemoteTrack,
  type RemoteTrackPublication,
  type RemoteParticipant
} from 'livekit-client'
import { CONTROL_TOPIC, type ConnectionState } from '../lib/constants'

export interface LiveKitState {
  connectionState: ConnectionState
  videoTrack: RemoteTrack | null
  rtt: number | null
  error: string | null
  connect: (url: string, token: string) => Promise<void>
  disconnect: () => void
  sendControl: (action: string, button?: number) => void
}

const encoder = new TextEncoder()
const decoder = new TextDecoder()

export function useLiveKit(): LiveKitState {
  const roomRef = useRef<Room | null>(null)
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [videoTrack, setVideoTrack] = useState<RemoteTrack | null>(null)
  const [rtt, setRtt] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const clearPing = useCallback(() => {
    if (pingTimer.current) {
      clearInterval(pingTimer.current)
      pingTimer.current = null
    }
  }, [])

  const reset = useCallback(() => {
    clearPing()
    setConnectionState('disconnected')
    setVideoTrack(null)
    setRtt(null)
    roomRef.current = null
  }, [clearPing])

  const sendControl = useCallback((action: string, button?: number) => {
    const room = roomRef.current
    if (!room) return
    const payload = button !== undefined
      ? JSON.stringify({ action, button })
      : JSON.stringify({ action })
    room.localParticipant.publishData(encoder.encode(payload), {
      reliable: true,
      topic: CONTROL_TOPIC
    })
  }, [])

  const connect = useCallback(async (url: string, token: string) => {
    if (roomRef.current) return
    setConnectionState('connecting')
    setError(null)

    const room = new Room()
    roomRef.current = room

    // Track events
    room.on(RoomEvent.TrackSubscribed, (track: RemoteTrack, _pub: RemoteTrackPublication, _p: RemoteParticipant) => {
      if (track.kind === Track.Kind.Video) setVideoTrack(track)
    })
    room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
      if (track.kind === Track.Kind.Video) setVideoTrack(null)
    })
    room.on(RoomEvent.Disconnected, reset)

    // RTT measurement: listen for pong replies
    room.on(RoomEvent.DataReceived, (payload: Uint8Array, _p: RemoteParticipant | undefined, _k: unknown, topic?: string) => {
      if (topic !== 'pong') return
      const sent = Number(decoder.decode(payload))
      if (sent) setRtt(performance.now() - sent)
    })

    try {
      await room.connect(url, token)
      setConnectionState('connected')

      // Send pings every 2s for RTT measurement
      pingTimer.current = setInterval(() => {
        room.localParticipant.publishData(
          encoder.encode(String(performance.now())),
          { reliable: false, topic: 'ping' }
        )
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
      reset()
    }
  }, [reset])

  const disconnect = useCallback(() => {
    if (!roomRef.current) return
    sendControl('release_all')
    roomRef.current.disconnect()
    reset()
  }, [sendControl, reset])

  useEffect(() => clearPing, [clearPing])

  return { connectionState, videoTrack, rtt, error, connect, disconnect, sendControl }
}
