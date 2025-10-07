import serial
import serial.tools.list_ports
from config import config
import time

class grbl_manager:
    def __init__(self):
        super().__init__()
        self.grbl = serial.Serial()
        self.grbl.baudrate = config.get("grbl","baudrate")
        self.grbl.timeout = config.get("grbl","timeout")
    
    def find_arduino_port(self):
        """Mencari port Arduino secara otomatis"""
        ports = serial.tools.list_ports.comports()
        keywords = [s.lower() for s in config.get("grbl","port_description")]
        for port in ports:
            desc = (port.description or "").lower()
            if any(k in desc for k in keywords):
                return port.device
        return None
    
    def connect_grbl(self):
        """Menghubungkan ke GRBL jika port Arduino ditemukan"""
        port = self.find_arduino_port()
        if port:
            try:
                self.grbl.port = port
                self.grbl.open()
                time.sleep(2)  
                self.grbl.write(b"\r\n\r\n")  
                time.sleep(2)
                self.grbl.flushInput()
                print(f"GRBL berhasil terhubung di port: {port}")
            except serial.SerialException as e:
                print("Error saat menghubungkan ke GRBL:", e)
        else:
            print("Arduino tidak ditemukan.")
