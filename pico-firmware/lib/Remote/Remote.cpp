#include "Remote.h"
#include <hardware/gpio.h>


void Remote::begin()
{
  for (size_t i = 0; i < buttonCount; i++)
  {
    gpio_init(allButtons[i]);
    gpio_put(allButtons[i], 0);                              // output value locked to low
    gpio_set_outover(allButtons[i], GPIO_OVERRIDE_LOW);       // hardware-force output low, ignore gpio_put
    gpio_disable_pulls(allButtons[i]);                        // no pull-up/pull-down
    gpio_set_dir(allButtons[i], GPIO_IN);                     // start released (high-Z)
  }
}

void Remote::press(Button btn)
{
  gpio_set_dir(btn, GPIO_OUT);
}

void Remote::release(Button btn)
{
  gpio_set_dir(btn, GPIO_IN);
}

void Remote::releaseAll()
{
  for (size_t i = 0; i < buttonCount; i++)
    gpio_set_dir(allButtons[i], GPIO_IN);
}

void Remote::tap(Button btn, uint32_t ms)
{
  press(btn);
  delay(ms);
  release(btn);
}

bool Remote::isPressed(Button btn)
{
  return gpio_get_dir(btn) == GPIO_OUT;
}

void Remote::printState()
{
  for (size_t i = 0; i < buttonCount; i++)
  {
    Serial.print(buttonNames[i]);
    Serial.print(isPressed(allButtons[i]) ? ":ON " : ":OFF ");
  }
  Serial.println();
}
