import serial
import time

"""
Simple serial instrument controller
Used to control an HP34401A
"""

class SerialInst:
    def __init__(self, port, baud):
        self.com = serial.Serial(port = port, baudrate = baud, timeout = 1)

    def write(self, cmd, timeout=0.5):
        self.com.write(cmd.encode('ascii') + b'\n')
        time.sleep(timeout)

    def read(self):
        return self.com.readline().decode('ascii').strip()

    def query(self, cmd, timeout=0.5):
        self.write(cmd, timeout)
        return self.read()