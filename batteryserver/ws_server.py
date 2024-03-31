import socket
import hashlib
import ubinascii
import network
import secrets
import battery


def accept_connection(server_socket):
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")

    # Perform the WebSocket handshake
    data = client_socket.recv(4096).decode('utf-8')
    headers = data.split("\r\n")

    # Extract key from headers
    key = ''
    for header in headers:
        if "Sec-WebSocket-Key" in header:
            key = header.split(": ")[1]

    # Generate the accept key
    accept_key = ubinascii.b2a_base64(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode("utf-8").strip()

    # Send the handshake response
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
    )
    print("Sending response to handshake", response.encode())
    client_socket.send(response.encode())

    return client_socket


def receive_data(client_socket):
    data = client_socket.recv(1024)

    print("Received data", data)

    if len(data) == 0:
        return None

    # Parse the WebSocket frame
    opcode_and_length = data[0]
    payload_length = opcode_and_length & 127

    if payload_length == 126:
        payload_length = int.from_bytes(data[2:4], byteorder='big')
        mask = data[4:8]
        payload = data[8:]
    elif payload_length == 127:
        payload_length = int.from_bytes(data[2:10], byteorder='big')
        mask = data[10:14]
        payload = data[14:]
    else:
        mask = data[2:6]
        payload = data[6:]

    decoded_payload = bytearray()
    for i in range(len(payload)):
        decoded_payload.append(payload[i] ^ mask[i % 4])

    return decoded_payload.decode('utf-8')


def send_data(client_socket, message):
    message = bytes(message, 'utf-8')
    message_length = len(message)
    send_data = bytearray([129])

    if message_length <= 125:
        send_data.append(message_length)
    elif message_length <= 65535:
        send_data.append(126)
        send_data += message_length.to_bytes(2, byteorder='big')
    else:
        send_data.append(127)
        send_data += message_length.to_bytes(8, byteorder='big')

    send_data += message

    return client_socket.send(send_data)


import time
from machine import Pin, ADC
from micropython import const
import neopixel


BATTERY_PIN = 10

RGB_DATA = const(48)
RGB_PWR = const(34)

# Create a NeoPixel instance
# Brightness of 0.3 is ample for the 1515 sized LED
pixel = neopixel.NeoPixel(Pin(RGB_DATA), 1)

# Create a colour wheel index int
color_index = 0

adc3 = ADC(Pin(BATTERY_PIN))  # Assign the ADC pin to read
adc3.atten(ADC.ATTN_11DB)


def websocket_server(host, port):
    global color_index
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"WebSocket server listening on {host}:{port}")

    pixel[0] = (255, 0, 0, 0.5)
    pixel.write()

    while True:
        client_socket = accept_connection(server_socket)

        while True:
            adc_value, battery_percentage, battery_voltage = battery.get_battery_percentage()
            message = "{" + f'"percent": {battery_percentage}, "voltage": {battery_voltage}, "adc": {adc_value}' + "}"
            send_bytes = send_data(client_socket, message)
            print(f"Sent: {message} ({send_bytes} bytes)")

            for i in range(66):
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
    return wlan.ifconfig()[0]


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


# Turn on the power to the NeoPixel
set_rgb_power(True)


print("Starting websocket demo")
print("Establishing wifi connection")
local_ip = do_connect()

websocket_server(local_ip, 8765)