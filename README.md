### Steps to deploy the project to an ESP32 S3 on Windows

1. Make sure python 3.10 is installed
2. Install esptool
   ```
   pip install esptool
   ```
3. Download micropython firmware from https://micropython.org/download/GENERIC_S3/
4. Flash your device and install the firmware with esptool
   ```
   esptool.py --chip esp32s3 --port COM3 erase_flash
   esptool.py --chip esp32s3 --port COM3 write_flash -z 0 "Downloads\GENERIC_S3-20220618-v1.19.1.bin"
   ```
5. To push to the board (press the reset button if necessary to put the board into its initial boot mode):
   ```
   python3 push.py
   ```
6. To view the serial output, use PuTTY and connect to serial port COM5

### Steps to deploy the project to an ESP32 S3 on Linux / Mac

1. Install python 3.9 use pyenv to update your `python` command from python 2 to 3
2. Install esptool
   ```
   pip install esptool
   ```
3. Download micropython firmware from https://micropython.org/download/GENERIC_S3/
4. Find the device name (could be /dev/tty.SLAB_USBtoUART or /dev/tty.usbserial-01613E00 or /dev/ttyACM0 or something similar)
5. Flash your device and install the firmware with esptool
   ```
   esptool.py --chip esp32 --port /dev/ttyACM0 erase_flash
   esptool.py --chip esp32s3 --port /dev/ttyACM0 write_flash -z 0 ESP32_GENERIC_S3-20240222-v1.22.2.bin
   ```
6. To push to the board (press the reset button if necessary to put the board into its initial boot mode):
   ```
   python3 push.py
   ```
7. To view files run
   ```bash
   python3 pyboard.py -f ls
   ```
8. To monitor the serial output, simply run:
   ```bash
   python3 pyboard.py
   ```
   Or, use picocom:
```bash
  picocom /dev/ttyACM0 -b115200
  (if the board is awake, just press return to get to the REPL)
  (to reset to the board, press ctrl-d)
  (to quit, press ctrl-a ctrl-x)
```

### Steps to set up IntelliJ IDEA

1. Install the Micropython plugin
2. Open the project. This will create a new Java project
3. Go to Project Structure
4. Choose the Python SDK as the project SDK
5. Go to Modules. You will see an existing "java" module
6. Remove this module
7. Click "+". Choose "Import module"
8. Choose the main project folder
9. When asked, select the Python SDK
10. Click Next > Next > Finish
11. Go to Facets
12. Click Add > Micropython Support
13. Select ESP8266 from the drop down
14. Untick "autodetect path" and enter the path to your device (e.g. `/dev/tty.usbserial-01613E00`)
15. Close the Project Structure dialog
