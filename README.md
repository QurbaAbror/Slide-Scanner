# Slide Scanner Application

Aplikasi Slide Scanner berbasis NiceGUI dengan interface yang modern dan responsif.

## Fitur Utama

### 1. Menu Bar
Menu bar terletak di bagian atas dengan dropdown menu yang mencakup:
- **File**: New Project, Open Project, Save Project, Import/Export Image, Exit
- **View**: Toggle Preview, Toggle Zoom Slider, Full Screen, Reset View
- **Tools**: Calibration, Measurement, Annotation, Image Analysis
- **Settings**: Camera Settings, Display Settings, Preferences, Advanced Settings
- **Help**: User Manual, Keyboard Shortcuts, Documentation, About

**Perbaikan Menu Dropdown:**
- Setiap menu dropdown sekarang muncul tepat di bawah tombol menu yang diklik
- Tidak ada lagi konflik antar menu (menu lain tidak ikut terbuka)
- Menggunakan `ui.dropdown_button` dengan `auto_close=True` untuk behavior yang lebih baik

### 2. Main Stream Area
- Area utama yang mencakup seluruh layar (kecuali menu bar)
- Background gradient yang menarik
- Placeholder untuk camera feed
- Informasi instruksi untuk pengguna

### 3. Pop-up Components

#### Preview Pop-up
- Terletak di kanan atas
- Ukuran: 300x200 pixels
- Dapat di-toggle melalui View menu
- Memiliki tombol close (×)
- Placeholder untuk preview stream

#### Zoom Slider Pop-up
- Terletak di kiri bawah
- Ukuran: 250x100 pixels
- Slider dengan range 0.1x - 5.0x
- Real-time zoom level display
- Dapat di-toggle melalui View menu
- Memiliki tombol close (×)

## Cara Menjalankan

1. Pastikan Python 3.7+ terinstall
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```bash
   python main.py
   ```
4. Buka browser dan akses: `http://localhost:5000`

## Struktur File

```
Slide Scanner/
├── main.py          # Entry point aplikasi
├── UI.py            # Komponen UI dan logika interface
├── requirements.txt # Dependencies
└── README.md        # Dokumentasi
```

## Teknologi yang Digunakan

- **NiceGUI**: Framework web UI untuk Python
- **Python 3.7+**: Bahasa pemrograman utama

## Pengembangan Selanjutnya

Aplikasi ini siap untuk dikembangkan lebih lanjut dengan menambahkan:
- Integrasi kamera real-time
- Sistem zoom yang fungsional
- Tools untuk calibration dan measurement
- Sistem annotation
- Export/import functionality
- Database integration

## Kontrol UI

- **Toggle Preview**: View → Toggle Preview atau gunakan menu
- **Toggle Zoom**: View → Toggle Zoom Slider atau gunakan menu
- **Close Pop-ups**: Klik tombol × di pojok kanan atas setiap pop-up
- **Zoom Control**: Gunakan slider di zoom pop-up untuk mengatur level zoom

## Catatan

- Pop-up components menggunakan positioning absolute dengan z-index tinggi
- Responsive design yang menyesuaikan dengan ukuran layar
- Notifikasi real-time untuk feedback pengguna
- Styling modern dengan shadow dan border radius
