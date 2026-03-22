import { useState, useCallback, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Spinner } from './ui/spinner'
import type { ConnectionState } from '../lib/constants'

const URL_STORAGE_KEY = 'remote-operator:livekit-url'

interface ConnectBarProps {
  connectionState: ConnectionState
  onConnect: (url: string, token: string) => void
  onDisconnect: () => void
  error: string | null
}

export function ConnectBar({ connectionState, onConnect, onDisconnect, error }: ConnectBarProps) {
  const [url, setUrl] = useState(() => localStorage.getItem(URL_STORAGE_KEY) || '')
  const [token, setToken] = useState('')

  useEffect(() => {
    if (url) localStorage.setItem(URL_STORAGE_KEY, url)
  }, [url])

  const handleConnect = useCallback(() => {
    if (!url.trim() || !token.trim()) return
    onConnect(url.trim(), token.trim())
  }, [url, token, onConnect])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && connectionState === 'disconnected') {
        handleConnect()
      }
    },
    [connectionState, handleConnect]
  )

  const isConnected = connectionState === 'connected'
  const isConnecting = connectionState === 'connecting'

  return (
    <div className="shrink-0 px-3 pb-3">
      <div className="flex gap-2 items-center">
        <Input
          placeholder="LiveKit URL (wss://...)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isConnected || isConnecting}
          className="w-64 font-mono text-xs"
        />
        <Input
          placeholder="Access Token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isConnected || isConnecting}
          className="flex-1 font-mono text-xs"
          type="password"
        />
        {isConnected ? (
          <Button variant="destructive" onClick={onDisconnect} className="shrink-0">
            Disconnect
          </Button>
        ) : (
          <Button
            variant="primary"
            onClick={handleConnect}
            disabled={isConnecting || !url.trim() || !token.trim()}
            className="shrink-0"
          >
            {isConnecting ? (
              <span className="flex items-center gap-2">
                <Spinner className="h-3 w-3" />
                Connecting
              </span>
            ) : (
              'Connect'
            )}
          </Button>
        )}
      </div>
      {error && (
        <p className="text-red-400 text-xs mt-1.5 px-1">{error}</p>
      )}
    </div>
  )
}
