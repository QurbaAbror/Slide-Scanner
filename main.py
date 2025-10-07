# File: main.py (Versi Lengkap dan Sudah Diperbaiki)

from nicegui import ui
import atexit
from starlette.responses import StreamingResponse

# Import dari file lokal Anda
from UI import create_ui
from camera_usb import CameraManager
from toupcam_manager import ToupcamStream
from grbl_manager import grbl_manager

# --- Inisialisasi Kamera (Tetap Global) ---
# Objek kamera dibuat sekali saat aplikasi pertama kali berjalan.
print("Menginisialisasi objek global...")
preview_camera = CameraManager(camera_index=0)
main_camera = ToupcamStream()
grbl = grbl_manager() # <-- NEW: Buat satu instance GRBL manager untuk seluruh aplikasi

# Daftarkan fungsi stop untuk dijalankan saat aplikasi ditutup
atexit.register(preview_camera.stop)
atexit.register(main_camera.stop_stream)
print("Inisialisasi global selesai.")

def connect_hardware():
    """Fungsi untuk menghubungkan semua perangkat keras."""
    print("🚀 Memulai koneksi hardware saat startup...")
    grbl.connect_grbl()

# --- Endpoints untuk Video Stream (Tidak Berubah) ---
# Endpoint ini khusus untuk menyediakan data gambar streaming.
@ui.page('/preview_feed')
def preview_feed():
    if not preview_camera.is_running:
        preview_camera.start()
    return StreamingResponse(preview_camera.jpeg_frame_generator(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

@ui.page('/main_feed')
def main_feed():
    if not main_camera.is_running:
        if main_camera.initialize_camera():
            main_camera.start_stream()
        else:
            # Handle jika kamera utama gagal diinisialisasi
            print("ERROR: Gagal menginisialisasi ToupCam.")
            return

    return StreamingResponse(main_camera.jpeg_frame_generator(),
                             media_type='multipart/x-mixed-replace; boundary=frame')


# --- Tampilan UI Utama (BAGIAN YANG DIPERBAIKI) ---
@ui.page('/')
def main_page():
    """
    Fungsi ini akan membuat UI baru untuk setiap klien yang terhubung.
    Ini menciptakan sesi pribadi yang memungkinkan 'await ui.run_javascript' berfungsi.
    """
    print("Membuat instance UI baru untuk klien...")
    # 1. Pembuatan UI dipanggil dari dalam fungsi ini
    app = create_ui()

    # 2. Logika untuk menghubungkan objek kamera ke UI juga ada di sini
    if app:
        # Menghubungkan objek kamera (yang global) ke instance UI klien ini
        app.main_camera = main_camera


# --- Menjalankan Aplikasi (Tidak Berubah) ---
if __name__ in {"__main__", "__mp_main__"}:
    print("Menjalankan aplikasi NiceGUI pada port 5000...")
    connect_hardware()
    ui.run(port=5000)