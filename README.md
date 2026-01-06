# 📡 WebGIS As-Built Digitizer

**Automated PDF to KMZ Converter for Fiber Optic Network Design**

Aplikasi WebGIS ini dirancang untuk mempermudah proses digitasi gambar *As-Built Drawing* (PDF) menjadi format Google Earth (.KMZ). Dilengkapi dengan fitur **Computer Vision** dan **OCR (Optical Character Recognition)** untuk mendeteksi aset jaringan (Tiang, FAT, FDT) secara otomatis.

> **Live Demo:** [Masukkan Link Streamlit App Anda Di Sini]
> **Integration:** Integrated with [Ruang Nalar Urban](https://ruangnalarurs.online)

---

## 🌟 Fitur Utama

### 1. 🗺️ PDF Georeferencing
- Overlay file PDF teknis di atas peta satelit (Google Satellite).
- Kontrol transparansi, skala, dan rotasi untuk mencocokkan gambar dengan kondisi lapangan.

### 2. 🤖 Auto-Digitize (Smart Detection)
- **Otomatisasi Penuh:** Menggunakan OpenCV dan Tesseract OCR untuk mendeteksi simbol Tiang, FAT, dan FDT.
- **Auto-Naming:** Membaca label teks dari PDF (contoh: "1A", "FOT145...") dan menamai titik KMZ secara otomatis.
- **Multi-Standard:** Mendukung konfigurasi penamaan yang dinamis (Linknet, Telkom, PLN, dll).

### 3. ✏️ Manual Digitizing Tools
- Drawing tools interaktif untuk menggambar jalur kabel (Fiber/Distribution) secara presisi.
- Mendukung *snapping* dan editing manual jika hasil otomasi perlu koreksi.

### 4. 📂 Existing Network Overlay
- Upload file `.KMZ` eksisting untuk melihat jaringan lama sebagai referensi agar tidak tumpang tindih.

---

## 🛠️ Teknologi yang Digunakan

Proyek ini dibangun menggunakan **Python** dengan library berikut:
* **Streamlit:** Framework UI Web.
* **Folium & Leaflet:** Peta interaktif.
* **OpenCV:** Pengolahan citra (deteksi bentuk lingkaran/kotak).
* **Tesseract OCR:** Pembacaan teks dari gambar.
* **SimpleKML:** Generator file KMZ.

---

## 🚀 Cara Menjalankan (Deployment)

Aplikasi ini dioptimalkan untuk berjalan di **Streamlit Cloud**.

### 1. Persiapan File
Pastikan repository GitHub memiliki struktur file berikut:

```text
/
├── app.py              # Kode utama aplikasi
├── requirements.txt    # Daftar library Python
├── packages.txt        # Daftar software sistem (Wajib untuk OCR)
└── README.md           # Dokumentasi ini
