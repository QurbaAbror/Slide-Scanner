# File: camera_manager.py

import cv2
import threading
import time

class CameraManager:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        # Kita hanya butuh menyimpan frame mentah terbaru
        self.latest_frame = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()

    def _capture_loop(self):
        print(f"INFO: Memulai capture loop untuk kamera...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"ERROR: Tidak bisa membuka kamera.")
            return

        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.latest_frame = frame
            time.sleep(0.05) # Tetap beri jeda agar CPU tidak 100%
        
        self.cap.release()

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        if not self.is_running: return
        self.is_running = False

    def jpeg_frame_generator(self):
        """Generator yang menghasilkan frame dalam format MJPEG."""
        print("INFO: Memulai MJPEG frame generator...")
        while True:
            frame = None
            with self.lock:
                if self.latest_frame is not None:
                    frame = self.latest_frame.copy()

            if frame is None:
                time.sleep(0.1)
                continue

            # Encode frame ke JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()

            # Hasilkan byte stream dengan format MJPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')