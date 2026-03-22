import { cn } from "@/lib/utils";
import type { ConnectionState } from "../lib/constants";
import type { VideoMeta } from "./video-display";

interface StatusBarProps {
  tab: "teleop" | "replay";
  connectionState: ConnectionState;
  isRecording: boolean;
  frameCount: number;
  rtt: number | null;
  videoMeta: VideoMeta | null;
  isReplayLoaded: boolean;
  replayTotalFrames: number;
  isReplayPlaying: boolean;
}

function LatencyDot({ rtt }: { rtt: number }) {
  const color = rtt < 100 ? "bg-emerald-500" : rtt < 200 ? "bg-amber-500" : "bg-red-500";
  return <div className={cn("w-1.5 h-1.5 rounded-full", color)} />;
}

function StatusDot({ color, pulse }: { color: string; pulse?: boolean }) {
  return <div className={cn("w-1.5 h-1.5 rounded-full", color, pulse && "animate-pulse")} />;
}

function TeleopStatus({ connectionState, rtt }: { connectionState: ConnectionState; rtt: number | null }) {
  if (rtt !== null) {
    return (
      <div className="flex items-center gap-1.5">
        <LatencyDot rtt={rtt} />
        <span className="text-white font-mono">{Math.round(rtt / 2)}ms</span>
      </div>
    );
  }

  const dot = connectionState === "connected"
    ? { color: "bg-emerald-500" }
    : connectionState === "connecting"
      ? { color: "bg-amber-500", pulse: true }
      : { color: "bg-white/20" };

  const label = connectionState === "connected" ? "Connected"
    : connectionState === "connecting" ? "Connecting"
    : "Disconnected";

  return (
    <div className="flex items-center gap-2">
      <StatusDot {...dot} />
      <span>{label}</span>
    </div>
  );
}

function ReplayStatus({ isLoaded, isPlaying }: { isLoaded: boolean; isPlaying: boolean }) {
  const color = isLoaded ? "bg-cyan-500" : "bg-white/20";
  const label = !isLoaded ? "No file loaded" : isPlaying ? "Playing" : "Paused";
  return (
    <div className="flex items-center gap-2">
      <StatusDot color={color} pulse={isPlaying} />
      <span>{label}</span>
    </div>
  );
}

export function StatusBar({
  tab, connectionState, isRecording, frameCount,
  rtt, videoMeta, isReplayLoaded, replayTotalFrames, isReplayPlaying,
}: StatusBarProps) {
  const teleop = tab === "teleop";

  return (
    <div className="shrink-0 pb-2 flex items-center justify-between text-[11px] text-white/30">
      <div className="flex items-center gap-3">
        {teleop
          ? <TeleopStatus connectionState={connectionState} rtt={rtt} />
          : <ReplayStatus isLoaded={isReplayLoaded} isPlaying={isReplayPlaying} />}

        {teleop && isRecording && (
          <span className="text-red-400/70 font-mono">{frameCount} frames</span>
        )}
        {teleop && videoMeta && videoMeta.width > 0 && (
          <span className="font-mono">{videoMeta.width}×{videoMeta.height} {videoMeta.fps}fps</span>
        )}
        {!teleop && isReplayLoaded && (
          <span className="font-mono">{frameCount + 1} / {replayTotalFrames}</span>
        )}
      </div>
    </div>
  );
}
