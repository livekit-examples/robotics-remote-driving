import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
import { BUTTONS, type ControlState } from '../lib/constants'
import type { McapFrame } from '../types/electron-api'

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

const EMPTY_HELD = new Set<number>()

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
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const indexRef = useRef(0)
  const framesRef = useRef<McapFrame[]>([])

  const isLoaded = frames.length > 0
  const totalFrames = frames.length
  const currentControls = isLoaded ? frames[currentIndex]?.controls ?? null : null

  const held = useMemo(
    () => (currentControls ? controlsToHeld(currentControls) : EMPTY_HELD),
    [currentControls]
  )

  const stopPlayback = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsPlaying(false)
  }, [])

  const startPlayback = useCallback(() => {
    if (framesRef.current.length === 0) return
    stopPlayback()
    setIsPlaying(true)

    intervalRef.current = setInterval(() => {
      const next = indexRef.current + 1
      if (next >= framesRef.current.length) {
        stopPlayback()
        return
      }
      indexRef.current = next
      setCurrentIndex(next)
    }, 33) // ~30fps
  }, [stopPlayback])

  const loadFrames = useCallback((data: McapFrame[]) => {
    stopPlayback()
    setFrames(data)
    framesRef.current = data
    setCurrentIndex(0)
    indexRef.current = 0
  }, [stopPlayback])

  const loadFile = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await window.electronAPI.openMcap()
      if (data) loadFrames(data)
    } finally {
      setIsLoading(false)
    }
  }, [loadFrames])

  const loadFromDrop = useCallback(async (path: string) => {
    setIsLoading(true)
    try {
      const data = await window.electronAPI.readMcap(path)
      loadFrames(data)
    } finally {
      setIsLoading(false)
    }
  }, [loadFrames])

  const togglePlayback = useCallback(() => {
    if (isPlaying) {
      stopPlayback()
    } else {
      if (indexRef.current >= framesRef.current.length - 1) {
        indexRef.current = 0
        setCurrentIndex(0)
      }
      startPlayback()
    }
  }, [isPlaying, startPlayback, stopPlayback])

  const seek = useCallback((index: number) => {
    const clamped = Math.max(0, Math.min(index, framesRef.current.length - 1))
    indexRef.current = clamped
    setCurrentIndex(clamped)
  }, [])

  const nextFrame = useCallback(() => {
    stopPlayback()
    seek(indexRef.current + 1)
  }, [seek, stopPlayback])

  const prevFrame = useCallback(() => {
    stopPlayback()
    seek(indexRef.current - 1)
  }, [seek, stopPlayback])

  const close = useCallback(() => {
    stopPlayback()
    setFrames([])
    framesRef.current = []
    setCurrentIndex(0)
    indexRef.current = 0
  }, [stopPlayback])

  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  return {
    frames, currentIndex, isPlaying, isLoaded, isLoading, totalFrames, held,
    loadFile, loadFromDrop, togglePlayback, seek, nextFrame, prevFrame, close
  }
}
