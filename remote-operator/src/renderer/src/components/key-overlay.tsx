import { cn } from '@/lib/utils'
import { BUTTONS } from '../lib/constants'

interface KeyOverlayProps {
  held: Set<number>
}

function KeyCap({
  label,
  active,
  className
}: {
  label: string
  active: boolean
  className?: string
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-center rounded-[3px] border font-mono text-xs font-bold uppercase',
        'transition-all duration-75 ease-out',
        active
          ? 'bg-cyan-500/90 border-cyan-400/80 text-white shadow-[0_0_20px_rgba(6,182,212,0.35)] scale-[0.96]'
          : 'bg-white/[0.06] border-white/[0.08] text-white/25',
        className
      )}
    >
      {label}
    </div>
  )
}

export function KeyOverlay({ held }: KeyOverlayProps) {
  return (
    <div className="absolute bottom-6 left-6 z-10">
      <div className="backdrop-blur-md bg-black/30 rounded-[3px] p-4 border border-white/[0.06]">
        <div className="flex flex-col items-center gap-2">
          {/* W key */}
          <div className="flex justify-center">
            <KeyCap label="W" active={held.has(BUTTONS.UP)} className="w-12 h-10" />
          </div>

          {/* A S D keys */}
          <div className="flex gap-2">
            <KeyCap label="A" active={held.has(BUTTONS.LEFT)} className="w-12 h-10" />
            <KeyCap label="S" active={held.has(BUTTONS.DOWN)} className="w-12 h-10" />
            <KeyCap label="D" active={held.has(BUTTONS.RIGHT)} className="w-12 h-10" />
          </div>

          {/* Speed and Brake */}
          <div className="flex gap-2 mt-1.5">
            <KeyCap
              label="SPEED"
              active={held.has(BUTTONS.SPEED)}
              className="w-[4.75rem] h-9 text-[10px]"
            />
            <KeyCap
              label="BRAKE"
              active={held.has(BUTTONS.BRAKE)}
              className="w-[4.75rem] h-9 text-[10px]"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
