import network
import requests
import secrets
import time


for i in range(10):
    print(f"Waiting {i}")
    time.sleep(1)


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


print("Starting now")

do_connect()

print("Connected")

print("Getting demo page")

x = requests.get('https://w3schools.com/python/demopage.htm')

print(x.text)

print("Done")
