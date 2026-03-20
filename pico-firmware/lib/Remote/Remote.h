#pragma once
#include <Arduino.h>

enum Button : uint8_t
{
  UP = 16,
  DOWN = 17,
  LEFT = 18,
  RIGHT = 19,
  SPEED = 20,
  BRAKE = 21,
};

static const Button allButtons[] = {UP, DOWN, LEFT, RIGHT, SPEED, BRAKE};
static const char *buttonNames[] = {"UP", "DOWN", "LEFT", "RIGHT", "SPEED", "BRAKE"};
static const size_t buttonCount = sizeof(allButtons) / sizeof(allButtons[0]);

class Remote
{
public:
  void begin();
  void press(Button btn);
  void release(Button btn);
  void releaseAll();
  void tap(Button btn, uint32_t ms = 100);
  bool isPressed(Button btn);
  void printState();
};
