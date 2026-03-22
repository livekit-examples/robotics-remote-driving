export interface ControlState {
  w: boolean
  a: boolean
  s: boolean
  d: boolean
  speed: boolean
  brake: boolean
}

export const DEFAULT_CONTROLS: ControlState = {
  w: false, a: false, s: false, d: false, speed: false, brake: false
}
