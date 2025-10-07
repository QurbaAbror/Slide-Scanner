import serial
import serial.tools.list_ports
from config import config

class grbl_manager:
    def __init__(self):
        super().__init__()
        self.grbl = serial.Serial()
        self.grbl.baudrate = config.get("grbl","baudrate")
        self.grbl.timeout = config.get("grbl","timeout")

        print(self.grbl.baudrate)
        print(self.grbl.timeout)