import time
import machine
from machine import Pin
import esp32
from lis3dh import Lis3dh
import telegram


led = Pin(23, Pin.OUT)


class Washing:

    def __init__(self):
        self.lis3dh = Lis3dh()


    def print_accel(self):
        self.lis3dh.get_accel()


def run():

    # check if the device woke from a deep sleep
    if machine.reset_cause() == machine.DEEPSLEEP_RESET:
        print('Woke from a deep sleep!')

    reason = machine.wake_reason()
    if reason == machine.TIMER_WAKE:
        # We woke due to the timer. Let's see if there are new config params to get
        pass


    washing = Washing()

    for i in range(0, 10):
        washing.print_accel()
        time.sleep(1)

    # lis_library()

    wake1 = Pin(32, mode=Pin.IN)
    esp32.wake_on_ext0(pin=wake1, level=esp32.WAKEUP_ANY_HIGH)

    # put the device to sleep for 15 seconds
    machine.deepsleep(15000)
