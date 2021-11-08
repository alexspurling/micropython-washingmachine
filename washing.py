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

LED_PIN = 23
INT_PIN = 32
BATTERY_EN_PIN = 14
BATTERY_PIN = 35


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
        battery_en_pin = Pin(BATTERY_EN_PIN, mode=Pin.OUT)
        battery_en_pin.on()

        # Sample 3 values from the ADC
        adc_values = []
        adc = ADC(Pin(BATTERY_PIN, mode=Pin.IN))
        adc.atten(ADC.ATTN_11DB)
        adc.width(ADC.WIDTH_12BIT)

        for i in range(0, 3):
            time.sleep(0.01)
            adcread = adc.read()
            print('adc read', adcread)
            adc_values.append(adcread)
        adc_value = sum(adc_values) / len(adc_values)

        battery_en_pin.off()

        adc_voltage = adc_value * 3.3 / 4095

        print('adc_voltage:', adc_voltage)

        # voltage divider uses 100k / 330k ohm resistors
        # 4.3V -> 3.223, 2.4 -> 1.842
        expected_max = 4.3*330/(100+330)
        expected_min = 2.8*330/(100+330)

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
        self.sleep(10 * 60 * 1000)

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

    def blink(self):
        while True:
            self.led.on()
            time.sleep(0.05)
            self.led.off()
            time.sleep(0.95)

    def start(self):

        # Threading support in micropython 1.17 is experimental but it seems to work
        _thread.start_new_thread(self.blink, (), {})

        self.load_settings()

        reason = machine.wake_reason()
        if reason == machine.TIMER_WAKE:
            print('Woke due to timer')
            self.check_new_params()
            self.send_notification()
            self.wait_for_next_wake()
        elif reason == machine.PIN_WAKE:
            print('Woke due to interrupt')
            self.check_new_params()
            self.send_notification()
            self.sleep_before_notification()

        # Loop required so that we can push new code
        # You need to reset (press the button) to get to this part
        for i in range(0, 30):
            print(i)
            time.sleep(1)

        self.wait_for_next_wake()


def run():
    washing_machine = WashingMachine()
    washing_machine.start()
