"""Button pin IDs and names — must match pico-firmware/lib/Remote/Remote.h."""

# Pin IDs
UP = 16
DOWN = 17
LEFT = 18
RIGHT = 19
SPEED = 20
BRAKE = 21

ALL_BUTTONS = {UP, DOWN, LEFT, RIGHT, SPEED, BRAKE}

BUTTON_NAMES = {
    UP: "UP", DOWN: "DOWN", LEFT: "LEFT",
    RIGHT: "RIGHT", SPEED: "SPEED", BRAKE: "BRAKE",
}

# Friendly name -> pin ID (used by remote-agent's release_control)
NAME_TO_PIN = {
    "forward": UP, "backward": DOWN,
    "left": LEFT, "right": RIGHT,
    "speed": SPEED, "brake": BRAKE,
}
