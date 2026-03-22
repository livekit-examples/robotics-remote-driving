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

export function useLiveKit(): LiveKitState {
  const roomRef = useRef<Room | null>(null)
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [videoTrack, setVideoTrack] = useState<RemoteTrack | null>(null)
  const [rtt, setRtt] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const sendControl = useCallback((action: string, button?: number) => {
    const room = roomRef.current
    if (!room) return

    const payload = button !== undefined
      ? JSON.stringify({ action, button })
      : JSON.stringify({ action })

    room.localParticipant.publishData(new TextEncoder().encode(payload), {
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

    room.on(
      RoomEvent.TrackSubscribed,
      (track: RemoteTrack, _pub: RemoteTrackPublication, _participant: RemoteParticipant) => {
        if (track.kind === Track.Kind.Video) {
          setVideoTrack(track)
        }
      }
    )

    room.on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
      if (track.kind === Track.Kind.Video) {
        setVideoTrack(null)
      }
    })

    room.on(RoomEvent.Disconnected, () => {
      setConnectionState('disconnected')
      setVideoTrack(null)
      setRtt(null)
      roomRef.current = null
      if (pingTimerRef.current) {
        clearInterval(pingTimerRef.current)
        pingTimerRef.current = null
      }
    })

    room.on(RoomEvent.DataReceived, (payload: Uint8Array, _participant: RemoteParticipant | undefined, _kind: unknown, topic?: string) => {
      if (topic === 'pong') {
        const sent = Number(new TextDecoder().decode(payload))
        if (sent) setRtt(performance.now() - sent)
      }
    })

    try {
      await room.connect(url, token)
      setConnectionState('connected')

      // Ping every 2s
      pingTimerRef.current = setInterval(() => {
        const ts = new TextEncoder().encode(String(performance.now()))
        room.localParticipant.publishData(ts, { reliable: false, topic: 'ping' })
      }, 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
      setConnectionState('disconnected')
      roomRef.current = null
    }
  }, [])

  const disconnect = useCallback(() => {
    if (!roomRef.current) return
    sendControl('release_all')
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current)
      pingTimerRef.current = null
    }
    roomRef.current.disconnect()
    roomRef.current = null
    setConnectionState('disconnected')
    setVideoTrack(null)
    setRtt(null)
  }, [sendControl])

  useEffect(() => {
    return () => {
      if (pingTimerRef.current) clearInterval(pingTimerRef.current)
    }
  }, [])

  return { connectionState, videoTrack, rtt, error, connect, disconnect, sendControl }
}
