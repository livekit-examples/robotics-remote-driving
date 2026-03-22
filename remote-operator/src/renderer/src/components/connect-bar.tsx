import { useState, useCallback } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Spinner } from "./ui/spinner";
import type { ConnectionState } from "../lib/constants";

const URL_STORAGE_KEY = "remote-operator:livekit-url";

interface ConnectBarProps {
  connectionState: ConnectionState;
  onConnect: (url: string, token: string) => void;
  onDisconnect: () => void;
  error: string | null;
}

function maskUrl(url: string): string {
  try {
    const u = new URL(url);
    return `${u.protocol}//•••••`;
  } catch {
    return "•••••";
  }
}

function persistUrl(url: string) {
  if (url) localStorage.setItem(URL_STORAGE_KEY, url);
}

export function ConnectBar({
  connectionState,
  onConnect,
  onDisconnect,
  error,
}: ConnectBarProps) {
  const [url, setUrl] = useState(
    () => localStorage.getItem(URL_STORAGE_KEY) || "",
  );
  const [token, setToken] = useState("");
  const [revealed, setRevealed] = useState(false);

  const handleUrlChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setUrl(value);
      persistUrl(value);
    },
    [],
  );

  const handleConnect = useCallback(() => {
    if (!url.trim() || !token.trim()) return;
    setRevealed(false);
    onConnect(url.trim(), token.trim());
  }, [url, token, onConnect]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && connectionState === "disconnected") {
        handleConnect();
      }
    },
    [connectionState, handleConnect],
  );

  const isConnected = connectionState === "connected";
  const isConnecting = connectionState === "connecting";

  return (
    <div className="shrink-0">
      {isConnected && !revealed ? (
        <div className="flex gap-2 items-center">
          <div
            onClick={() => setRevealed(true)}
            className="flex-1 flex gap-2 items-center cursor-pointer group"
          >
            <div className="h-10 flex items-center px-4 rounded-[3px] border border-white/10 bg-white/5 font-mono text-xs text-white/30 group-hover:border-white/20 transition-colors">
              {maskUrl(url)}
            </div>
            <div className="h-10 flex-1 flex items-center px-4 rounded-[3px] border border-white/10 bg-white/5 font-mono text-xs text-white/30 group-hover:border-white/20 transition-colors">
              •••••••••
            </div>
          </div>
          <Button
            variant="destructive"
            onClick={onDisconnect}
            className="shrink-0"
          >
            Disconnect
          </Button>
        </div>
      ) : (
        <div className="flex gap-2 items-center">
          <Input
            placeholder="LiveKit URL (wss://...)"
            value={url}
            onChange={handleUrlChange}
            onKeyDown={handleKeyDown}
            disabled={isConnected || isConnecting}
            className="w-72 font-mono text-xs"
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
            <Button
              variant="destructive"
              onClick={onDisconnect}
              className="shrink-0"
            >
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
                "Connect"
              )}
            </Button>
          )}
        </div>
      )}
      {error && <p className="text-red-400 text-xs mt-2 px-1">{error}</p>}
    </div>
  );
}
