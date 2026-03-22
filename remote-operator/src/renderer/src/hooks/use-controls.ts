import { useState, useEffect, useCallback, useRef } from 'react'
import { BUTTONS, DEFAULT_CONTROLS, type ControlState } from '../lib/constants'

const KEY_MAP: Record<string, number> = {
  w: BUTTONS.UP,
  a: BUTTONS.LEFT,
  s: BUTTONS.DOWN,
  d: BUTTONS.RIGHT,
  Tab: BUTTONS.SPEED,
  ' ': BUTTONS.BRAKE
}

export function heldToControls(held: Set<number>): ControlState {
  return {
    w: held.has(BUTTONS.UP),
    a: held.has(BUTTONS.LEFT),
    s: held.has(BUTTONS.DOWN),
    d: held.has(BUTTONS.RIGHT),
    speed: held.has(BUTTONS.SPEED),
    brake: held.has(BUTTONS.BRAKE)
  }
}

export interface ControlsState {
  held: Set<number>
  releaseAll: () => void
}

export function useControls(
  sendControl: (action: string, button?: number) => void,
  enabled: boolean
): ControlsState {
  const [held, setHeld] = useState<Set<number>>(new Set())
  const heldRef = useRef<Set<number>>(new Set())
  const sendControlRef = useRef(sendControl)
  sendControlRef.current = sendControl

  const releaseAll = useCallback(() => {
    if (heldRef.current.size > 0) {
      sendControlRef.current('release_all')
      heldRef.current = new Set()
      setHeld(new Set())
      window.electronAPI?.sendControls(DEFAULT_CONTROLS)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.repeat) return
      const pin = KEY_MAP[e.key]
      if (pin === undefined) return
      e.preventDefault()

      if (!heldRef.current.has(pin)) {
        const next = new Set(heldRef.current)
        next.add(pin)
        heldRef.current = next
        setHeld(next)
        sendControlRef.current('press', pin)
        window.electronAPI?.sendControls(heldToControls(next))
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      const pin = KEY_MAP[e.key]
      if (pin === undefined) return
      e.preventDefault()

      if (heldRef.current.has(pin)) {
        const next = new Set(heldRef.current)
        next.delete(pin)
        heldRef.current = next
        setHeld(next)
        sendControlRef.current('release', pin)
        window.electronAPI?.sendControls(heldToControls(next))
      }
    }

    const handleBlur = () => {
      if (heldRef.current.size > 0) {
        sendControlRef.current('release_all')
        heldRef.current = new Set()
        setHeld(new Set())
        window.electronAPI?.sendControls(DEFAULT_CONTROLS)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    window.addEventListener('blur', handleBlur)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
      window.removeEventListener('blur', handleBlur)
      if (heldRef.current.size > 0) {
        sendControlRef.current('release_all')
      }
    }
  }, [enabled])

  return { held, releaseAll }
}
