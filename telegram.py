import network
import time
import microWebCli as MicroWebCli
import secrets


def current_milli_time():
    return round(time.time_ns() / 1000000)


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f'Connecting to {secrets.WIFI_SSID}')
        wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        loop = 0
        while not wlan.isconnected():
            print(f'Connecting... {loop}')
            time.sleep(0.1)
            loop += 1
    print('network config:', wlan.ifconfig())


def get_bot():
    url = f'api.telegram.org/bot{secrets.TELEGRAM_API_KEY}/getMe'
    return MicroWebCli.GETRequest(url)


def send_message():
    url = 'https://api.telegram.org/bot/sendMessage'
    data = {
        'chat_id': secrets.TELEGRAM_CHAT_ID,
        'text': 'Yo dawg its me'
    }
    return MicroWebCli.JSONRequest(url, data)


start = current_milli_time()
do_connect()
time_taken = current_milli_time() - start
print(f'Connected in: {time_taken}ms')



print('telegram done')