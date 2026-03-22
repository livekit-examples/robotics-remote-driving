import type { ControlState } from '../types/electron-api'

// Mirrors car-protocol/buttons.py
export const BUTTONS = {
  UP: 16,
  DOWN: 17,
  LEFT: 18,
  RIGHT: 19,
  SPEED: 20,
  BRAKE: 21
} as const

export const CONTROL_TOPIC = 'control'

export type ConnectionState = 'disconnected' | 'connecting' | 'connected'

export const DEFAULT_CONTROLS: ControlState = {
  w: false, a: false, s: false, d: false, speed: false, brake: false
}

export type { ControlState }
