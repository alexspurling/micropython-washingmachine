
DEVICE="/dev/tty.usbserial-01613E00"

mpremote connect $DEVICE cp main.py :main.py
mpremote connect $DEVICE cp washing.py :washing.py

mpremote connect $DEVICE run main.py