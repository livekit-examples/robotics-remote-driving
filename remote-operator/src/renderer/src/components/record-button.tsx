import { cn } from '@/lib/utils'

interface RecordButtonProps {
  isRecording: boolean
  frameCount: number
  elapsed: number
  onStart: () => void
  onStop: () => void
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

export function RecordButton({ isRecording, frameCount, elapsed, onStart, onStop }: RecordButtonProps) {
  if (isRecording) {
    return (
      <button
        onClick={onStop}
        className="absolute top-4 right-4 z-10 flex items-center gap-3 px-4 py-2.5 rounded-xl bg-black/60 backdrop-blur-md border border-red-500/30 hover:border-red-500/50 transition-all cursor-pointer group"
      >
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse-record" />
          <span className="text-red-400 text-xs font-bold font-mono tracking-wider">REC</span>
        </div>
        <div className="w-px h-4 bg-white/10" />
        <span className="text-white/60 text-xs font-mono">{formatTime(elapsed)}</span>
        <div className="w-px h-4 bg-white/10" />
        <span className="text-white/40 text-xs font-mono">{frameCount}f</span>
        <div className="w-px h-4 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
        <span className="text-white/30 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity">
          click to stop
        </span>
      </button>
    )
  }

  return (
    <button
      onClick={onStart}
      className="absolute top-4 right-4 z-10 flex items-center gap-2 px-3.5 py-2 rounded-xl bg-black/40 backdrop-blur-md border border-white/[0.08] hover:border-white/20 hover:bg-black/60 transition-all cursor-pointer"
    >
      <div className="w-3 h-3 rounded-full border-2 border-white/30" />
      <span className="text-white/40 text-xs font-medium">Record</span>
    </button>
  )
}
