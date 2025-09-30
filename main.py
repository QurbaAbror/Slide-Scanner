# File: main.py

from nicegui import ui
import atexit
from starlette.responses import StreamingResponse

from UI import create_ui
from camera_usb import CameraManager # Untuk preview USB cam
from toupcam_manager import ToupcamStream # <-- UBAH NAMA KELAS YANG DIIMPOR

# --- Inisialisasi Kamera ---
preview_camera = CameraManager(camera_index=0)
atexit.register(preview_camera.stop)

main_camera = ToupcamStream() # <-- GUNAKAN KELAS BARU ANDA
# Kita akan panggil start() dari dalam endpoint agar lebih aman
atexit.register(main_camera.stop_stream)

# --- Endpoints ---
@ui.page('/preview_feed')
def preview_feed():
    if not preview_camera.is_running:
        preview_camera.start()
    return StreamingResponse(preview_camera.jpeg_frame_generator(),
                           media_type='multipart/x-mixed-replace; boundary=frame')

@ui.page('/main_feed')
def main_feed():
    # Inisialisasi dan mulai stream hanya saat endpoint ini pertama kali diakses
    if not main_camera.is_running:
        if main_camera.initialize_camera():
            main_camera.start_stream()
        else:
            # Jika kamera gagal, kita bisa tampilkan gambar error
            # (Untuk sekarang, biarkan kosong saja)
            return

    return StreamingResponse(main_camera.jpeg_frame_generator(),
                           media_type='multipart/x-mixed-replace; boundary=frame')

# --- Jalankan Aplikasi ---
app = create_ui()

# Connect camera to app for snapshot functionality
if app:
    app.main_camera = main_camera

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=5000)