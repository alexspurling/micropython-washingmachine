import time
import machine
from machine import Pin, ADC
import esp32
from lis3dh import Lis3dh
import telegram
import network
import secrets
import json
import _thread
import neopixel
import bees3

LED_PIN = 34
INT_PIN = 7
BATTERY_EN_PIN = 14
BATTERY_PIN = 35
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

    def get_battery_percentage(self):

        adc_voltage = bees3.get_battery_voltage()

        print('adc_voltage:', adc_voltage)

        # voltage divider uses 100k / 330k ohm resistors
        # 4.3V -> 3.223, 2.4 -> 1.842
        # expected_max = 4.3*330/(100+330)
        # expected_min = 2.8*330/(100+330)

        expected_max = 4.2
        expected_min = 3.1

        battery_level = (adc_voltage - expected_min) / (expected_max - expected_min)
        return battery_level * 100.0

    def send_notification(self):
        do_connect()
        print('Sending notification...')
        battery = self.get_battery_percentage()
        print('Battery:', battery)
        result = telegram.send_message(f'Washing done! Battery {battery:.2f}%')
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
        bees3.set_rgb_power(True)

        pixel = neopixel.NeoPixel(Pin(bees3.RGB_DATA), 1)
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

        print('Starting LED thread')
        self.blink(1)

        reason = machine.wake_reason()

        print('Got wake reason: ', reason)
        if reason == machine.TIMER_WAKE:
            self.blink(1)
            print('Woke due to timer')
            self.check_new_params()
            self.send_notification()
            self.wait_for_next_wake()
        elif reason == machine.PIN_WAKE:
            self.blink(2)
            print('Woke due to interrupt')
            self.check_new_params()
            # self.send_notification()
            self.sleep_before_notification()

        print('Sleeping for 30 seconds')
        # Loop required so that we can push new code
        # You need to reset (press the button) to get to this part
        for i in range(0, 30):
            print(i)
            time.sleep(1)

        print('Going to sleep')

        self.wait_for_next_wake()


def run():
    washing_machine = WashingMachine()
    washing_machine.start()
