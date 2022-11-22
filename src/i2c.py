from machine import I2C, Pin


class I2CDevice:

    def __init__(self, id, scl, sda):
        self.id = id
        self.i2c = I2C(0, scl=Pin(scl), sda=Pin(sda), freq=100000)

    def read_reg(self, reg_addr):
        """
        Read a single byte from the given address
        """
        return self.i2c.readfrom_mem(self.id, reg_addr, 1)[0]

    def write_reg(self, reg_addr, data):
        """
        Write a single byte to the given address
        """
        return self.i2c.writeto_mem(self.id, reg_addr, bytes([data]))

    def read_data(self, addr, num_bytes):
        """
        Read multiple bytes from the given address
        """
        return self.i2c.readfrom_mem(self.id, addr, num_bytes)
