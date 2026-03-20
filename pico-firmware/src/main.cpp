#include <Remote.h>

Remote remote;
uint32_t lastCmd = 0;

void setup()
{
  Serial.begin(115200);
  remote.begin();
}

void loop()
{
  while (Serial.available())
  {
    uint8_t cmd = Serial.read();
    lastCmd = millis();

    if (cmd == 0x00)
    {
      remote.releaseAll();
      continue;
    }

    bool isRelease = cmd & 0x80;
    uint8_t pin = cmd & 0x7F;

    if (pin < 16 || pin > 21)
      continue;

    Button btn = static_cast<Button>(pin);

    if (isRelease)
      remote.release(btn);
    else
      remote.press(btn);
  }

  // Watchdog: release all if no command received in 500ms
  if (lastCmd > 0 && millis() - lastCmd > 500)
  {
    remote.releaseAll();
    lastCmd = 0;
  }
}
