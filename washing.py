import time
from machine import Pin

led = Pin(23, Pin.OUT)


def run():
    while True:
        led.on()
        time.sleep(0.02)
        led.off()
        time.sleep(0.02)
