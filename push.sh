
DEVICE="/dev/tty.SLAB_USBtoUART"
# or maybe DEVICE="/dev/tty.usbserial-01613E00"

mpremote connect $DEVICE cp secrets.py :secrets.py
mpremote connect $DEVICE cp main.py :main.py
mpremote connect $DEVICE cp washing.py :washing.py
mpremote connect $DEVICE cp i2c.py :i2c.py
mpremote connect $DEVICE cp lis3dh.py :lis3dh.py
mpremote connect $DEVICE cp telegram.py :telegram.py
mpremote connect $DEVICE cp microWebCli.py :microWebCli.py

mpremote connect $DEVICE run main.py