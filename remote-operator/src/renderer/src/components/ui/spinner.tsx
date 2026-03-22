import { cn } from '@/lib/utils'

export function Spinner({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-full border-2 border-white/10 border-t-cyan-500 animate-spin', className)} />
  )
}
