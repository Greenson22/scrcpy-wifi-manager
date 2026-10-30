# Scrcpy & ADB Wi-Fi Controller (Clay Edition)

Aplikasi GUI modern berbasis **PyQt6** untuk menghubungkan perangkat Android via ADB Wi-Fi dan menjalankan `scrcpy` dengan estetika **Claymorphism (Clay Style)** yang lembut dan elegan. 

Aplikasi ini dirancang **Cross-Platform (Linux & Windows)**.

---

## 🚀 Fitur Utama

1. **Kemudahan Input IP & Port**:
   - **Smart Auto-Split**: Jika mengetik atau menempel format `192.168.1.100:5555` di kolom IP, port otomatis dipisah ke kolom Port.
   - **Tombol "📋 Paste"**: 1-klik paste dari clipboard dengan pemisahan cerdas.
   - **Tombol "🌐 IP Lokal"**: Mengisi 3 blok pertama subnet komputer lokal (misal: `192.168.1.`) secara otomatis.
   - **Riwayat Perangkat**: Menyimpan daftar perangkat sebelumnya untuk dipilih cepat.
   - **Tombol "🔍 Cek Devices"**: Memeriksa perangkat yang aktif via `adb devices -l`.

2. **Fleksibilitas Mode Tampilan**:
   - **Layar Primer / Mirror (Copy)**:
     - Opsi matikan layar fisik HP (`--turn-screen-off`).
     - Opsi cegah HP tidur (`--stay-awake`).
   - **Multi-Layar Sekunder (Virtual Display)**:
     - Dukungan menambahkan **lebih dari 1 layar sekunder** secara bersamaan.
     - Setiap layar sekunder dapat diberi nama kustom dan resolusi/DPI kustom (atau memilih dari preset yang tersedia).
     - Checkbox Aktif/Nonaktif per layar sekunder.

3. **Claymorphism Aesthetic**:
   - Card putih lembut dengan sudut membulat (*border-radius 20px*).
   - Efek 3D clay empuk menggunakan bayangan lembut (*soft drop shadow*).
   - Segmented Pill Switcher untuk pergantian mode.

4. **Auto-Save & Auto-Load (`config.json`)**:
   - Seluruh pengaturan tersimpan otomatis dan dimuat kembali saat aplikasi dibuka.

---

## 🐧 Cara Menjalankan di LINUX

### 1. Prasyarat
Pastikan `adb` dan `scrcpy` sudah terpasang:
```bash
sudo apt install scrcpy adb   # Debian/Ubuntu
# atau instalasi sesuai distro Anda
```

### 2. Jalankan Aplikasi
```bash
cd scrcpy-wifi-manager
./.venv/bin/python3 main.py
```

---

## 🪟 Cara Menjalankan di WINDOWS

Aplikasi ini sudah dioptimalkan khusus untuk Windows:
- **No CMD Flash**: Tidak ada jendela Command Prompt hitam yang berkedip saat menekan tombol ADB.
- **Pencarian Binary Otomatis**: Bisa mendeteksi `adb.exe` / `scrcpy.exe` dari PATH sistem maupun jika file `.exe` ditaruh langsung di folder proyek ini.

### Cara Cepat (1-Klik via Batch File):
Cukup **klik dua kali** file:
👉 `run_windows.bat`
*(File ini akan otomatis membuat `.venv`, menginstal dependensi, dan langsung meluncurkan GUI)*.

### Cara Manual via Command Prompt / PowerShell:
1. Pastikan sudah mengunduh **scrcpy untuk Windows** dari rilis resmi Genymobile. Masukkan file `scrcpy.exe` dan `adb.exe` ke folder ini atau tambahkan ke PATH Windows.
2. Buat virtual environment & install dependensi:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```cmd
   python main.py
   ```
   *(Atau jalankan `pythonw main.py` jika ingin tanpa jendela konsol).*
