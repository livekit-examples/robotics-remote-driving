import { cn } from '@/lib/utils'
import type { ConnectionState } from '../lib/constants'

function StatusDot({ color, pulse }: { color: string; pulse?: boolean }) {
  return <div className={cn('w-1.5 h-1.5 rounded-full', color, pulse && 'animate-pulse')} />
}

interface StatusBarProps {
  tab: 'teleop' | 'replay'
  connectionState: ConnectionState
  isRecording: boolean
  frameCount: number
  isReplayLoaded: boolean
  replayTotalFrames: number
  isReplayPlaying: boolean
}

export function StatusBar({
  tab, connectionState, isRecording, frameCount,
  isReplayLoaded, replayTotalFrames, isReplayPlaying
}: StatusBarProps) {
  const teleop = tab === 'teleop'

  let dot: { color: string; pulse?: boolean }
  let label: string

  if (teleop) {
    dot = connectionState === 'connected' ? { color: 'bg-emerald-500' }
      : connectionState === 'connecting' ? { color: 'bg-amber-500', pulse: true }
      : { color: 'bg-white/20' }
    label = connectionState === 'connected' ? 'Connected'
      : connectionState === 'connecting' ? 'Connecting'
      : 'Disconnected'
  } else {
    dot = isReplayLoaded
      ? { color: 'bg-cyan-500', pulse: isReplayPlaying }
      : { color: 'bg-white/20' }
    label = isReplayLoaded
      ? isReplayPlaying ? 'Playing' : 'Paused'
      : 'No file loaded'
  }

  return (
    <div className="shrink-0 h-8 px-4 flex items-center justify-between text-[11px] text-white/30 border-t border-white/[0.04]">
      <div className="flex items-center gap-1.5">
        <StatusDot {...dot} />
        <span>{label}</span>
      </div>

      <div className="flex items-center gap-3">
        {teleop && isRecording && (
          <span className="text-red-400/70 font-mono">{frameCount} frames</span>
        )}
        {!teleop && isReplayLoaded && (
          <span className="font-mono">{frameCount + 1} / {replayTotalFrames}</span>
        )}
        <span className="font-mono">
          {teleop ? 'WASD + Tab + Space' : 'Space to play/pause'}
        </span>
      </div>
    </div>
  )
}
