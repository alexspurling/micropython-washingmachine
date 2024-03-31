import battery
import time


while True:
    print('battery_percentage:', battery.get_battery_percentage())
    time.sleep(1)

