import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import { BUTTONS, type ControlState } from '../lib/constants'
import type { McapFrame } from '../types/electron-api'

const FRAME_INTERVAL = 33 // ms (~30fps)
const EMPTY_HELD = new Set<number>()

export interface ReplayState {
  frames: McapFrame[]
  currentIndex: number
  isPlaying: boolean
  isLoaded: boolean
  isLoading: boolean
  totalFrames: number
  held: Set<number>
  loadFile: () => Promise<void>
  loadFromDrop: (path: string) => Promise<void>
  togglePlayback: () => void
  seek: (index: number) => void
  nextFrame: () => void
  prevFrame: () => void
  close: () => void
}

function controlsToHeld(c: ControlState): Set<number> {
  const s = new Set<number>()
  if (c.w) s.add(BUTTONS.UP)
  if (c.a) s.add(BUTTONS.LEFT)
  if (c.s) s.add(BUTTONS.DOWN)
  if (c.d) s.add(BUTTONS.RIGHT)
  if (c.speed) s.add(BUTTONS.SPEED)
  if (c.brake) s.add(BUTTONS.BRAKE)
  return s
}

export function useReplay(): ReplayState {
  const [frames, setFrames] = useState<McapFrame[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const raf = useRef(0)
  const lastTime = useRef(0)
  const idx = useRef(0)
  const data = useRef<McapFrame[]>([])

  const isLoaded = frames.length > 0
  const totalFrames = frames.length
  const controls = isLoaded ? frames[currentIndex]?.controls ?? null : null
  const held = useMemo(() => (controls ? controlsToHeld(controls) : EMPTY_HELD), [controls])

  // --- Playback ---

  const stopPlayback = useCallback(() => {
    if (raf.current) cancelAnimationFrame(raf.current)
    raf.current = 0
    setIsPlaying(false)
  }, [])

  const startPlayback = useCallback(() => {
    if (data.current.length === 0) return
    stopPlayback()
    setIsPlaying(true)
    lastTime.current = 0

    const tick = (now: number) => {
      if (!lastTime.current) lastTime.current = now

      if (now - lastTime.current >= FRAME_INTERVAL) {
        lastTime.current = now
        const next = idx.current + 1
        if (next >= data.current.length) { stopPlayback(); return }
        idx.current = next
        setCurrentIndex(next)
      }
      raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
  }, [stopPlayback])

  // --- Navigation ---

  const seek = useCallback((index: number) => {
    const clamped = Math.max(0, Math.min(index, data.current.length - 1))
    idx.current = clamped
    setCurrentIndex(clamped)
  }, [])

  const nextFrame = useCallback(() => { stopPlayback(); seek(idx.current + 1) }, [seek, stopPlayback])
  const prevFrame = useCallback(() => { stopPlayback(); seek(idx.current - 1) }, [seek, stopPlayback])

  const togglePlayback = useCallback(() => {
    if (isPlaying) { stopPlayback(); return }
    // Restart from beginning if at end
    if (idx.current >= data.current.length - 1) {
      idx.current = 0
      setCurrentIndex(0)
    }
    startPlayback()
  }, [isPlaying, startPlayback, stopPlayback])

  // --- Loading ---

  const loadFrames = useCallback((mcap: McapFrame[]) => {
    stopPlayback()
    data.current = mcap
    idx.current = 0
    setFrames(mcap)
    setCurrentIndex(0)
  }, [stopPlayback])

  const loadFile = useCallback(async () => {
    setIsLoading(true)
    try {
      const result = await window.electronAPI.openMcap()
      if (result) loadFrames(result)
    } finally {
      setIsLoading(false)
    }
  }, [loadFrames])

  const loadFromDrop = useCallback(async (path: string) => {
    setIsLoading(true)
    try {
      loadFrames(await window.electronAPI.readMcap(path))
    } finally {
      setIsLoading(false)
    }
  }, [loadFrames])

  const close = useCallback(() => {
    stopPlayback()
    data.current = []
    idx.current = 0
    setFrames([])
    setCurrentIndex(0)
  }, [stopPlayback])

  useEffect(() => () => { if (raf.current) cancelAnimationFrame(raf.current) }, [])

  return {
    frames, currentIndex, isPlaying, isLoaded, isLoading, totalFrames, held,
    loadFile, loadFromDrop, togglePlayback, seek, nextFrame, prevFrame, close
  }
}
