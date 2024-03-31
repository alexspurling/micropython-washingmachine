import time
from lis3dh import Lis3dh

lis3dh = Lis3dh()

while True:
    lis3dh.get_accel()
    time.sleep(1)

