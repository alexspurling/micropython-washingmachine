### Steps to deploy the project to an ESP32

1. Install python 3.9 use pyenv to update your `python` command from python 2 to 3
2. Install esptool
   ```
   pip install esptool
   ```
3. Download micropython firmware from https://micropython.org/download/esp32
4. Flash your device and install the firmware with esptool
   ```
   esptool.py --chip esp32 --port /dev/tty.usbserial-01613E00 erase_flash
   esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32-20210902-v1.17.bin
   ```
5. Install mpremote
   ```
   pip install mpremote
   ```
6. Connect to the device
   ```
   $ mpremote connect /dev/tty.usbserial-01613E00 ls
   ls :
   139 boot.py
   143 main.py
   ```
7. Run the `push.sh` script
   ```
   $ ./push.py
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