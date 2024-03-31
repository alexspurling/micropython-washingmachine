from micropython import const
import time
import neopixel
from machine import Pin

RGB_DATA = const(48)
RGB_PWR = const(34)


def set_rgb_power(state):
    """Enable or Disable power to the second LDO"""
    Pin(RGB_PWR, Pin.OUT).value(state)


# NeoPixel rainbow colour wheel
def rgb_color_wheel(wheel_pos):
    """Color wheel to allow for cycling through the rainbow of RGB colors."""
    wheel_pos = wheel_pos % 255

    if wheel_pos < 85:
        return 255 - wheel_pos * 3, 0, wheel_pos * 3
    elif wheel_pos < 170:
        wheel_pos -= 85
        return 0, wheel_pos * 3, 255 - wheel_pos * 3
    else:
        wheel_pos -= 170
        return wheel_pos * 3, 255 - wheel_pos * 3, 0


# Create a NeoPixel instance
# Brightness of 0.3 is ample for the 1515 sized LED
pixel = neopixel.NeoPixel(Pin(RGB_DATA), 1)

# Create a colour wheel index int
color_index = 0

# Turn on the power to the NeoPixel
set_rgb_power(True)


# Rainbow colours on the NeoPixel
while True:
    # Get the R,G,B values of the next colour
    r, g, b = rgb_color_wheel(color_index)
    # Set the colour on the NeoPixel
    pixel[0] = (r, g, b, 0.5)
    pixel.write()
    # Increase the wheel index
    color_index += 1

    # If the index == 255, loop it
    if color_index == 255:
        color_index = 0
        # Invert the internal LED state every half colour cycle

    # Sleep for 15ms so the colour cycle isn't too fast
    time.sleep(0.015)


