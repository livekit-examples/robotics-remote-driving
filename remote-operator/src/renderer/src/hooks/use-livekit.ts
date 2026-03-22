import { useState, useCallback, useRef } from 'react'
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
  error: string | null
  connect: (url: string, token: string) => Promise<void>
  disconnect: () => void
  sendControl: (action: string, button?: number) => void
}

export function useLiveKit(): LiveKitState {
  const roomRef = useRef<Room | null>(null)
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [videoTrack, setVideoTrack] = useState<RemoteTrack | null>(null)
  const [error, setError] = useState<string | null>(null)

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
      roomRef.current = null
    })

    try {
      await room.connect(url, token)
      setConnectionState('connected')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
      setConnectionState('disconnected')
      roomRef.current = null
    }
  }, [])

  const disconnect = useCallback(() => {
    if (!roomRef.current) return
    sendControl('release_all')
    roomRef.current.disconnect()
    roomRef.current = null
    setConnectionState('disconnected')
    setVideoTrack(null)
  }, [sendControl])

  return { connectionState, videoTrack, error, connect, disconnect, sendControl }
}
