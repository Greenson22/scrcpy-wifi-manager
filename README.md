# Scrcpy & ADB Wi-Fi Manager (Clay Style)

Aplikasi GUI modern berbasis **PyQt6** untuk menghubungkan perangkat Android via ADB Wi-Fi dan menjalankan `scrcpy` dengan estetika **Claymorphism (Clay Style)** yang lembut dan empuk.

## Fitur Utama

1. **Kemudahan Input IP & Port**:
   - **Smart Auto-Split**: Jika Anda menempelkan (*paste*) atau mengetik teks berformat `192.168.1.100:5555` di kolom IP, port akan otomatis terpisah ke kolom Port.
   - **Tombol "📋 Paste"**: Sekali klik mendeteksi clipboard dan memisahkan IP:Port.
   - **Tombol "🌐 IP Lokal"**: Mendeteksi otomatis subnet PC Anda (misal `192.168.1.`) sehingga tinggal mengetik digit terakhir.
   - **Riwayat Perangkat**: Menyimpan daftar perangkat terakhir yang pernah digunakan.
   - **Tombol "🔍 Cek Devices"**: Memeriksa perangkat yang aktif via `adb devices`.

2. **Fleksibilitas Mode Tampilan**:
   - **Layar Primer / Mirror (Copy)**:
     - Opsi mematikan layar HP fisik saat mirror (`--turn-screen-off`).
     - Opsi menjaga HP tetap menyala (`--stay-awake`).
   - **Multi-Layar Sekunder (Virtual Display)**:
     - Dukungan menambahkan **lebih dari 1 layar sekunder** secara bersamaan.
     - Setiap layar sekunder dapat diberi nama kustom dan resolusi/DPI kustom (atau memilih dari preset yang tersedia seperti Portrait, Landscape, Tablet).
     - Tombol centang *Aktif* untuk memilih layar mana saja yang ingin dibuka saat tombol dijalankan.

3. **Claymorphism Aesthetic**:
   - Tampilan visual modern dengan sudut sangat membulat (*rounded corners*), warna pastel lembut, dan efek bayangan mengambang (*soft clay drop shadows*).

4. **Auto-Save & Auto-Load (`config.json`)**:
   - Seluruh pengaturan tersimpan otomatis dan dimuat kembali saat aplikasi dibuka.

---

## Cara Menjalankan

### Prasyarat Sistem
Pastikan `adb` dan `scrcpy` sudah terpasang di sistem Linux Anda:
```bash
adb version
scrcpy --version
```

### Menjalankan Aplikasi
Masuk ke folder proyek dan jalankan via virtual environment:
```bash
cd /home/lemon-manis-22/Projects/Python3/scrcpy-wifi-manager
./.venv/bin/python3 main.py
```
Atau jika virtual environment telah diaktifkan:
```bash
source .venv/bin/activate
python main.py
```
