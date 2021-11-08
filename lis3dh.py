from i2c import I2CDevice
import time
import struct


class Lis3dh(I2CDevice):

    ID = 0x19
    SCL = 22
    SDA = 21
    WHO_AM_I = 0x0f
    WHO_AM_I_ID = 0x33

    CTRL_REG1 = 0x20  # Data rate selection and X, Y, Z axis enable register
    CTRL_REG2 = 0x21  # High pass filter selection
    CTRL_REG3 = 0x22  # Control interrupts
    CTRL_REG4 = 0x23  # BDU
    CTRL_REG5 = 0x24  # FIFO enable / latch interrupts

    INT1_CFG = 0x30  # Interrupt 1 config
    INT1_SRC = 0x31  # Interrupt status - read in order to reset the latch
    INT1_THS = 0x32  # Define threshold in mg to trigger interrupt
    INT1_DURATION = 0x33  # Define duration for the interrupt to be recognised (not sure about this one)

    # Read this value to set the reference values against which accel values are compared when calculating
    # a threshold interrupt. Also called the REFERENCE register in the datasheet
    HP_FILTER_RESET = 0x26

    REG_X = 0x28
    REG_Y = 0x2A
    REG_Z = 0x2C

    def __init__(self):
        super().__init__(self.ID, self.SCL, self.SDA)
        self.init()

    def init(self):
        print('Initialising accelerometer')
        self.self_check()

        self.write_reg(self.CTRL_REG5, 0x80)

        time.sleep(0.1)

        # Set data rate to 1hz, low power mode off, enable X, Y and Z axes
        # 00100111
        self.write_reg(self.CTRL_REG1, 0b00010111)

        # 1 - BDU: Block data update. This ensures that both the high and the low bytes for each
        #          16bit represent the same sample
        # 0 - BLE: Big/little endian. Set to little endian
        # 00 - FS1-FS0: Full scale selection. 00 represents +-2g
        # 1 - HR: High resolution mode enabled.
        # 00 - ST1-ST0: Self test. Disabled
        # 0 - SIM: SPI serial interface mode. Default is 0
        self.write_reg(self.CTRL_REG4, 0x88)

        # 2 Write 09h into CTRL_REG2 // High-pass filter enabled on data and interrupt1
        self.write_reg(self.CTRL_REG2, 0x09)

        # 3 Write 40h into CTRL_REG3 // Interrupt driven to INT1 pad
        self.write_reg(self.CTRL_REG3, 0x40)

        # 4 Write 00h into CTRL_REG4 // FS = 2 g
        # 5 Write 08h into CTRL_REG5 // Interrupt latched

        # // Threshold as a multiple of 16mg. 4 * 16 = 64mg
        self.set_sensitivity(2)

        # Duration the acceleration must be above the threshold before triggering the
        # interrupt. 50/1hz = 5s
        self.set_duration(5)

        # Read the reference register to set the reference acceleration values against which
        # we compare current values for interrupt generation
        # 8 Read HP_FILTER_RESET
        self.read_reg(self.HP_FILTER_RESET)

        # 9 Write 2Ah into INT1_CFG // Configure interrupt when any of the X, Y or Z axes exceeds
        #   (rather than stay below) the threshold
        self.write_reg(self.INT1_CFG, 0x2a)

        print("Accelerometer enabled")

    def self_check(self):
        who_am_i = self.read_reg(self.WHO_AM_I)
        if who_am_i != self.WHO_AM_I_ID:
            raise Exception(f'Did not get expected whoami id from Lis3dh I2C device: {who_am_i}')

    def set_sensitivity(self, threshold):
        # Threshold as a multiple of 16mg. 4 * 16 = 64mg
        self.write_reg(self.INT1_THS, threshold)

    def set_duration(self, duration):
        # Duration the acceleration must be above the threshold before triggering the
        # interrupt. 5/1hz = 5s
        self.write_reg(self.INT1_DURATION, duration)

    def get_accel(self):

        accel_data = self.read_data(self.REG_X | 0x80, 6)
        x, y, z = struct.unpack('<hhh', accel_data)

        print('Got accel data:', x, y, z)
