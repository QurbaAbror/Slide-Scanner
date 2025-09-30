from nicegui import ui
from camera_usb import CameraManager
import os
from datetime import datetime
import base64

class SlideScanner:
    def __init__(self):
        self.preview_visible = True
        self.zoom_slider_visible = False
        self.zoom_level = 1.0
        self.preview_popup = None
        self.zoom_popup = None
        self.zoom_slider = None
        self.zoom_label = None
        self.main_stream_source = 'toupcam'
        self.preview_stream_source = 'usb_camera'
        self.main_stream_widget = None
        self.preview_widget = None
        self.main_camera = None  # Will be set from main.py

        # Gallery untuk snapshot dan opened images
        self.gallery_popup = None
        self.gallery_container = None
        self.gallery_images = []  # List untuk menyimpan path gambar
        self.snapshot_counter = 0
    
    def switch_streams(self):
        """Menukar sumber URL antara widget utama dan preview."""
        # Pastikan kedua widget sudah ada
        if not self.main_stream_widget or not self.preview_widget:
            print("ERROR: Widget stream belum siap untuk ditukar.")
            return

        print("🔄 Menukar stream...")
        # 1. Ambil URL sumber saat ini dari kedua widget
        main_src = self.main_stream_widget.source
        preview_src = self.preview_widget.source

        # 2. Tukar sumber URL di kedua widget
        self.main_stream_widget.set_source(preview_src)
        self.preview_widget.set_source(main_src)

        print(f"   Tampilan Utama sekarang: {preview_src}")
        print(f"   Tampilan Preview sekarang: {main_src}")

    def capture_snapshot(self):
        """Capture snapshot from ToupCam camera"""
        if not self.main_camera:
            ui.notify('Camera not initialized', type='negative')
            return

        # Create snapshots directory if it doesn't exist
        snapshot_dir = 'snapshots'
        if not os.path.exists(snapshot_dir):
            os.makedirs(snapshot_dir)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{snapshot_dir}/snapshot_{timestamp}.jpg'

        # Get current frame and save it (with thread safety)
        import cv2
        frame_to_save = None
        with self.main_camera.lock:
            if self.main_camera.current_frame is not None:
                frame_to_save = self.main_camera.current_frame.copy()

        if frame_to_save is not None:
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame_to_save, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, frame_bgr)
            ui.notify(f'Snapshot saved: {filename}', type='positive')
            print(f'✅ Snapshot saved: {filename}')

            # Add to gallery
            self.add_image_to_gallery(filename)
        else:
            ui.notify('No frame available to capture', type='warning')
            print('⚠️ No frame available to capture')

    def add_image_to_gallery(self, image_path):
        """Add image to gallery popup with a remove button and no fullscreen click."""
        if not self.gallery_container:
            return

        self.gallery_images.append(image_path)

        with self.gallery_container:
            # Tangkap referensi kartu dengan 'as card'
            with ui.card().classes('gallery-thumbnail-card') as card:
                # 1. TOMBOL 'X' BARU DITAMBAHKAN DI SINI
                ui.icon('close').classes('remove-image-btn') \
                    .on('click', lambda p=image_path, c=card: self.remove_image_from_gallery(p, c)) \
                    .tooltip('Remove image from gallery')

                # 2. .on('click', ...) DIHAPUS DARI ui.image
                # Sekarang klik pada gambar tidak akan melakukan apa-apa
                ui.image(image_path).classes('thumbnail-image')

                # Label dengan filename
                filename = os.path.basename(image_path)
                ui.label(filename).classes('text-xs text-gray-400 w-full text-center truncate') \
                                  .style('max-width: 180px;')

        if self.gallery_popup:
            self.gallery_popup.style('display: flex;')

        print(f'📸 Image added to gallery: {image_path}')
    
    def remove_image_from_gallery(self, image_path, card_element):
        """Removes a specific image and its card from the gallery."""
        # Hapus elemen UI (kartu thumbnail)
        card_element.delete()

        # Hapus path gambar dari list data
        if image_path in self.gallery_images:
            self.gallery_images.remove(image_path)
        
        print(f'❌ Image removed from gallery: {os.path.basename(image_path)}')


    async def open_image_file(self):
        """Open image file from disk"""
        # Use NiceGUI's upload component
        result = await ui.run_javascript('''
            return new Promise((resolve) => {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.onchange = (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        const reader = new FileReader();
                        reader.onload = (event) => {
                            resolve({name: file.name, data: event.target.result});
                        };
                        reader.readAsDataURL(file);
                    } else {
                        resolve(null);
                    }
                };
                input.click();
            });
        ''')

        if result:
            # Save uploaded file to snapshots directory
            import base64
            snapshot_dir = 'snapshots'
            if not os.path.exists(snapshot_dir):
                os.makedirs(snapshot_dir)

            # Extract base64 data
            if ',' in result['data']:
                base64_data = result['data'].split(',')[1]
                image_data = base64.b64decode(base64_data)

                # Save file
                filename = f"{snapshot_dir}/{result['name']}"
                with open(filename, 'wb') as f:
                    f.write(image_data)

                ui.notify(f"Image opened: {result['name']}", type='positive')
                print(f'📂 Image opened: {filename}')

                # Add to gallery
                self.add_image_to_gallery(filename)
    

def create_ui():
    # Create instance of SlideScanner class
    app = SlideScanner()

    # Add custom CSS for full screen layout and pop-ups
    ui.add_head_html('''
    <style>
        /* Hilangkan scroll di seluruh halaman */
        html, body {
            margin: 0;
            padding: 0;
            overflow: hidden !important;
            height: 100vh;
            width: 100vw;
        }

        .preview-popup {
            position: fixed;
            top: 65px;
            right: 20px;
            width: 200px;
            height: 112px;
            background: rgba(40, 40, 40, 0.85);
            backdrop-filter: blur(5px);
            border: 1px solid #555;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            flex-direction: column;
            padding: 0;
            overflow: hidden;
        }

        .gallery-popup {
            position: fixed;
            top: 187px;  /* 65px (top preview) + 112px (height preview) + 10px (gap) */
            right: 20px;
            width: 200px;
            max-height: calc(100vh - 207px);  /* Sisa tinggi layar */
            background: rgba(40, 40, 40, 0.85);
            backdrop-filter: blur(5px);
            border: 1px solid #555;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            flex-direction: column;
            padding: 10px;
            overflow-y: auto;  /* Scrollable jika banyak gambar */
            overflow-x: hidden;
            display: none;  /* Hidden by default */
        }

        .gallery-popup::-webkit-scrollbar {
            width: 6px;
        }

        .gallery-popup::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 3px;
        }

        .gallery-popup::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 3px;
        }

        .gallery-popup::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
        
        .gallery-thumbnail-card {
            width: 100%;
            padding: 5px;
            margin: 0;
            box-sizing: border-box; /* Memastikan padding tidak menambah lebar */
            position: relative;
        }
        
        .remove-image-btn {
            position: absolute;
            top: 2px;
            right: 2px;
            color: #bbb;
            background-color: rgba(0, 0, 0, 0.4);
            border-radius: 50%;
            padding: 2px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .remove-image-btn:hover {
            color: #fff;
            background-color: rgba(255, 0, 0, 0.7);
            transform: scale(1.1);
        }

        .thumbnail-image {
            width: 100%;              /* Lebar gambar mengisi 100% dari card */
            height: 120px;            /* TINGGI TETAP, ini kuncinya! */
            object-fit: contain;      /* Membuat gambar muat tanpa terpotong */
            background-color: #2a2a2a; /* Warna latar belakang untuk 'letterboxing' */
            border-radius: 4px;       /* Sedikit lengkungan di sudut */
            cursor: pointer;
        }

        .zoom-popup {
            position: fixed;
            bottom: 20px;
            left: 20px;
            width: 250px;
            background: rgba(40, 40, 40, 0.85);
            backdrop-filter: blur(5px);
            border: 1px solid #555;
            border-radius: 12px;
            z-index: 1000;
            padding: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            display: none;
        }

        /* === GAYA BARU UNTUK TOMBOL CLOSE === */
        .close-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            color: #aaa;
            cursor: pointer;
            padding: 2px;
            border-radius: 50%;
            transition: all 0.2s ease-in-out;
        }

        .close-btn:hover {
            color: #fff;
            background-color: rgba(255, 255, 255, 0.2);
        }

        .popup-title {
            font-size: 16px;
            font-weight: bold;
            color: #eee;
            margin-bottom: 10px;
        }

        /* Main stream container - NO SCROLL */
        .main-stream-container {
            width: 100vw;
            height: calc(100vh - 45px);
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #fff;
            overflow: hidden;
        }

        .stream-image-box {
            width: 1000px;
            height: 836px;
            object-fit: contain;
        }
    </style>
    ''')

    # Create menu bar (smaller size)
    with ui.header().classes('bg-gray-800 text-white').style('height: 45px; min-height: 45px;'):
        with ui.row().classes('w-full justify-between items-center h-full'):
            ui.label('🔬 Slide Scanner').classes('text-base font-bold ml-2')

            with ui.row().classes('gap-1 mr-2'):
                # === File menu ===
                with ui.dropdown_button('File', icon='folder', auto_close=True).props('flat size=sm').classes('text-white text-sm'):
                    ui.item('New Project', on_click=lambda: ui.notify('New Project created'))
                    ui.item('Open Project', on_click=lambda: ui.notify('Open Project dialog'))
                    ui.item('Save Project', on_click=lambda: ui.notify('Project saved'))
                    ui.separator()
                    ui.item('📂 Open Image', on_click=lambda: app.open_image_file())
                    ui.item('Export Image', on_click=lambda: ui.notify('Export Image dialog'))
                    ui.separator()
                    ui.item('Exit', on_click=lambda: ui.notify('Exit application'))

                # === View menu ===
                with ui.dropdown_button('View', icon='visibility', auto_close=True).props('flat size=sm').classes('text-white text-sm'):
                    ui.item('Toggle Preview', on_click=lambda: toggle_preview(app))
                    ui.item('Toggle Gallery', on_click=lambda: toggle_gallery(app))
                    ui.item('Toggle Zoom Slider', on_click=lambda: toggle_zoom_slider(app))
                    ui.separator()
                    ui.item('Full Screen', on_click=lambda: ui.notify('Full Screen mode activated'))
                    ui.item('Reset View', on_click=lambda: ui.notify('View reset to default'))

                # === Camera menu ===
                with ui.dropdown_button('Camera', icon='videocam', auto_close=True).props('flat size=sm').classes('text-white text-sm'):
                    # Capture snapshot
                    ui.item('📷 Capture Snapshot', on_click=lambda: app.capture_snapshot())
                    ui.separator()
                    # Memanggil metode switch_streams dari objek 'app'
                    ui.item('🔄 Switch Streams', on_click=lambda: app.switch_streams())
                    ui.separator()
                    # Memanggil fungsi show_stream_status dengan objek 'app'
                    ui.item('📊 Stream Status', on_click=lambda: show_stream_status(app))
                    ui.separator()

                # === Tools menu ===
                with ui.dropdown_button('Tools', icon='build', auto_close=True).props('flat size=sm').classes('text-white text-sm'):
                    ui.item('Calibration', on_click=lambda: ui.notify('Calibration tool opened'))
                    ui.item('Measurement', on_click=lambda: ui.notify('Measurement tool opened'))
                    ui.item('Annotation', on_click=lambda: ui.notify('Annotation tool opened'))
                    ui.separator()
                    ui.item('Image Analysis', on_click=lambda: ui.notify('Image Analysis tool'))

                # === Settings menu ===
                with ui.dropdown_button('Settings', icon='settings', auto_close=True).props('flat size=sm').classes('text-white text-sm'):
                    ui.item('Camera Settings', on_click=lambda: ui.notify('Camera Settings opened'))
                    ui.item('Display Settings', on_click=lambda: ui.notify('Display Settings opened'))
                    ui.item('Preferences', on_click=lambda: ui.notify('Preferences opened'))
                    ui.separator()
                    ui.item('Advanced Settings', on_click=lambda: ui.notify('Advanced Settings'))

                # === Help menu ===
                with ui.dropdown_button('Help', icon='help', auto_close=True).props('flat size=sm').classes('text-white text-sm'):
                    ui.item('User Manual', on_click=lambda: ui.notify('User Manual opened'))
                    ui.item('Keyboard Shortcuts', on_click=lambda: ui.notify('Keyboard Shortcuts'))
                    ui.item('Documentation', on_click=lambda: ui.notify('Documentation opened'))
                    ui.separator()
                    ui.item('About', on_click=lambda: ui.notify('About Slide Scanner v1.0'))

    # === WIDGET UTAMA UNTUK STREAM KAMERA ===
    # Container dengan background hitam, NO SCROLL
    with ui.element('div').classes('main-stream-container'):
        # Image dengan ukuran fixed kotak (ratio 2448:2048 ≈ 1.2:1)
        # Width: 700px, Height: 585px (700/585 ≈ 1.196 ≈ 2448/2048)
        app.main_stream_widget = ui.image('/main_feed').classes('stream-image-box')


    # Create preview popup
    app.preview_popup = ui.element('div').classes('preview-popup')
    with app.preview_popup:
        # Tombol close baru tanpa judul
        ui.icon('close').classes('close-btn').on('click', lambda: hide_preview(app))
        app.preview_widget = ui.image('/preview_feed').style('width: 100%; height: 100%; object-fit: contain;')

    # Create gallery popup (di bawah preview)
    app.gallery_popup = ui.element('div').classes('gallery-popup')
    with app.gallery_popup:
        # Tombol close
        ui.icon('close').classes('close-btn').on('click', lambda: hide_gallery(app))
        # Title
        ui.label('Gallery').classes('text-sm font-bold text-white mb-2')
        # Container untuk images (scrollable)
        app.gallery_container = ui.column().style('width: 100%; gap: 10px;')

    # Create zoom popup
    app.zoom_popup = ui.element('div').classes('zoom-popup')
    with app.zoom_popup:
        # Tombol close baru tanpa judul
        ui.icon('close').classes('close-btn').on('click', lambda: hide_zoom_slider(app))

        # Slider tetap ada di sini
        app.zoom_slider = ui.slider(min=0.1, max=5.0, value=1.0, step=0.1, on_change=lambda e: on_zoom_change(app, e))
        app.zoom_label = ui.label(f'Zoom: {app.zoom_level:.1f}x').classes('text-sm text-gray-400 mt-2') # Ubah warna teks agar kontras

    # Return app instance so it can be accessed from main.py
    return app


def toggle_preview(app):
    """Toggle preview pop-up visibility"""
    app.preview_visible = not app.preview_visible
    if app.preview_visible:
        app.preview_popup.style('display: flex;')
    else:
        app.preview_popup.style('display: none;')

def hide_preview(app):
    """Hide preview pop-up"""
    app.preview_visible = False
    app.preview_popup.style('display: none;')

def toggle_gallery(app):
    """Toggle gallery pop-up visibility"""
    current_display = app.gallery_popup._props.get('style', '')
    if 'display: none' in current_display or not current_display:
        app.gallery_popup.style('display: flex;')
    else:
        app.gallery_popup.style('display: none;')

def hide_gallery(app):
    """Hide gallery pop-up"""
    app.gallery_popup.style('display: none;')

def toggle_zoom_slider(app):
    """Toggle zoom slider pop-up visibility"""
    app.zoom_slider_visible = not app.zoom_slider_visible
    if app.zoom_slider_visible:
        app.zoom_popup.style('display: block;')
    else:
        app.zoom_popup.style('display: none;')

def hide_zoom_slider(app):
    """Hide zoom slider pop-up"""
    app.zoom_slider_visible = False
    app.zoom_popup.style('display: none;')

def on_zoom_change(app, e):
    """Handle zoom slider changes"""
    app.zoom_level = e.value
    app.zoom_label.text = f'Zoom: {app.zoom_level:.1f}x'


# Fungsi ini sekarang membaca state dari objek 'app'
def show_stream_status(app: SlideScanner):
    """Show current stream status based on the app's state."""
    status_text = f"""
    Stream Status:
    - Main View: {app.main_stream_source.upper()}
    - Preview View: {app.preview_stream_source.upper()}
    """
    # Kita kembalikan notifikasi untuk fungsi ini karena sangat berguna untuk debugging
    ui.notify(status_text, multi_line=True, type='info', position='center')


