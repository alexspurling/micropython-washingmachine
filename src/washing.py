import time
import machine
from machine import Pin
from micropython import const
import esp32
from lis3dh import Lis3dh
import telegram
import network
import secrets
import json
import neopixel


RGB_LED_PIN = const(48)
LED_PIN = const(34)
INT_PIN = const(17)
BATTERY_EN_PIN = 14
BATTERY_PIN = 10
DELAY_BEFORE_NOTIFICATION = 40  # 40 mins


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f'Connecting to {secrets.WIFI_SSID}')
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        loop = 0
        while not wlan.isconnected():
            print(f'Connecting... {loop}')
            time.sleep(0.5)
            loop += 1
    print('network config:', wlan.ifconfig())


class WashingMachine:

    def __init__(self):
        self.led = Pin(LED_PIN, mode=Pin.OUT)
        self.led.on()
        self.lis3dh = Lis3dh()
        self.settings_file = 'settings.json'

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
        except Exception:
            settings = {}

        if settings:
            sensitivity = settings['sensitivity']
            duration = settings['duration']
            print(f'Setting sensitivity to {sensitivity}, duration to {duration}')
            self.lis3dh.set_sensitivity(sensitivity)
            self.lis3dh.set_duration(duration)

    def save_settings(self, sensitivity, duration):
        settings = {'sensitivity': sensitivity, 'duration': duration}
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        self.load_settings()

    def print_accel(self):
        self.lis3dh.get_accel()

    def check_new_params(self):
        do_connect()
        messages = telegram.get_messages()

        print('Got messages: ', messages)
        if messages.get('result'):
            last_message = messages['result'][-1]['message']

            print('Last message:', last_message)
            text = last_message['text']
            import re
            pattern = re.compile('/set ([0-9]+) ([0-9]+)')
            match = pattern.match(text)
            if match:
                sensitivity = int(match.group(1))
                duration = int(match.group(2))
                self.save_settings(sensitivity, duration)

    def send_notification(self):
        do_connect()
        print('Sending notification...')
        battery, battery_voltage = self.get_battery_percentage()
        print('Battery:', battery)
        result = telegram.send_message(f'Washing done! Battery {battery:.2f}% ({battery_voltage:.2f}V)')
        print(result)

    def sleep_before_notification(self):
        self.sleep(DELAY_BEFORE_NOTIFICATION * 60 * 1000)

    def wait_for_next_wake(self):
        wake1 = Pin(INT_PIN, mode=Pin.IN)
        esp32.wake_on_ext0(pin=wake1, level=esp32.WAKEUP_ANY_HIGH)
        self.sleep()

    def sleep(self, time=None):
        self.led.off()
        print('Going to sleep')
        if time is not None:
            machine.deepsleep(time)
        else:
            machine.deepsleep()

    def blink(self, times):
        Pin(LED_PIN, Pin.OUT).on()

        pixel = neopixel.NeoPixel(Pin(RGB_LED_PIN), 1)
        pixel[0] = (0, 0, 255, 1)
        pixel.write()

        for i in range(times):
            self.led.on()
            pixel[0] = (0, 0, 255, 1)
            pixel.write()
            time.sleep(0.05)
            self.led.off()
            time.sleep(0.3)

    def start(self):

        print('Device woke')
        self.blink(1)

        reason = machine.wake_reason()

        print('Got wake reason: ', reason)
        if reason == machine.TIMER_WAKE:
            self.blink(1)
            print('Woke due to timer')
            print('Checking for new params')
            self.check_new_params()
            print('Sending notification')
            self.send_notification()
        elif reason == machine.PIN_WAKE:
            self.blink(2)
            print('Woke due to interrupt')
            # self.check_new_params()
            # self.send_notification()
            print('Going to deepsleep')
            self.sleep_before_notification()
        else:
            print('Sleeping for 30 seconds')
            # Loop required so that we can push new code
            # You need to reset (press the button) to get to this part
            for i in range(0, 30):
                print(i)
                time.sleep(1)

        print('Loading accelerometer settings before going to sleep')
        self.load_settings()

        print('Going to deepsleep')
        self.wait_for_next_wake()


def run():
    washing_machine = WashingMachine()
    washing_machine.start()
