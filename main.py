import sys
import json
import os
import re
import socket
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QCheckBox, 
    QComboBox, QTextEdit, QGroupBox, QMessageBox,
    QRadioButton, QButtonGroup, QScrollArea, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QColor, QFont, QClipboard

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "ip": "",
    "port": "5555",
    "history": [],
    "mode": "mirror",  # "mirror" atau "virtual"
    "mirror_turn_screen_off": False,
    "mirror_stay_awake": True,
    "virtual_displays": [
        {
            "name": "Display 1 (Vertical)",
            "res": "1200x2133/512",
            "enabled": True
        }
    ],
    "no_audio": True,
    "bitrate": "4M"
}

PRESETS = [
    ("Custom", ""),
    ("HD Portrait (1080x1920/320)", "1080x1920/320"),
    ("HD Landscape (1920x1080/320)", "1920x1080/320"),
    ("Tablet Portrait (1200x2133/512)", "1200x2133/512"),
    ("Tablet Landscape (2133x1200/512)", "2133x1200/512"),
    ("Small Portable (720x1280/240)", "720x1280/240")
]

CLAY_STYLESHEET = """
QWidget {
    background-color: #EBF0F7;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    color: #2D3748;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #E2E8F0;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QGroupBox {
    background-color: #FFFFFF;
    border-radius: 20px;
    border: 1px solid #E2E8F0;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    font-weight: 700;
    font-size: 13px;
    color: #1E293B;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    background-color: transparent;
    color: #3B82F6;
}

QLineEdit, QComboBox {
    background-color: #F1F5F9;
    border: 2px solid transparent;
    border-radius: 12px;
    padding: 7px 12px;
    font-size: 13px;
    color: #1E293B;
}
QLineEdit:focus, QComboBox:focus {
    background-color: #FFFFFF;
    border: 2px solid #818CF8;
}

QPushButton {
    background-color: #F1F5F9;
    color: #334155;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #E2E8F0;
    color: #0F172A;
}
QPushButton:pressed {
    background-color: #CBD5E1;
}

QPushButton#btnPrimary {
    background-color: #6366F1;
    color: #FFFFFF;
    border: none;
    border-radius: 14px;
    padding: 12px 18px;
    font-weight: bold;
    font-size: 14px;
}
QPushButton#btnPrimary:hover {
    background-color: #4F46E5;
}
QPushButton#btnPrimary:pressed {
    background-color: #4338CA;
}

QPushButton#btnSuccess {
    background-color: #10B981;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton#btnSuccess:hover {
    background-color: #059669;
}

QPushButton#btnDanger {
    background-color: #FEE2E2;
    color: #DC2626;
    border: 1px solid #FECACA;
    border-radius: 10px;
    padding: 5px 10px;
    font-weight: bold;
}
QPushButton#btnDanger:hover {
    background-color: #FCA5A5;
    color: #991B1B;
}

QCheckBox, QRadioButton {
    font-size: 13px;
    spacing: 8px;
    color: #334155;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 2px solid #CBD5E1;
    background-color: #F8FAFC;
}
QRadioButton::indicator {
    border-radius: 10px;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

QTextEdit#logOutput {
    background-color: #0F172A;
    color: #38BDF8;
    border-radius: 16px;
    border: 1px solid #1E293B;
    padding: 12px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
}

QFrame.clayCard {
    background-color: #F8FAFC;
    border-radius: 16px;
    border: 1px solid #E2E8F0;
    padding: 10px;
}
"""

def add_clay_shadow(widget, blur=18, offset_y=4, alpha=35):
    """Menambahkan efek bayangan claymorphism lembut"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)

class DisplayItemWidget(QFrame):
    """Widget baris untuk setiap Virtual Display Sekunder"""
    def __init__(self, data, parent_gui, on_remove):
        super().__init__()
        self.parent_gui = parent_gui
        self.on_remove = on_remove
        self.setProperty("class", "clayCard")
        self.initUI(data)

    def initUI(self, data):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Baris atas: Aktifkan, Nama, Tombol Hapus
        top_layout = QHBoxLayout()
        self.chk_enabled = QCheckBox("Aktif")
        self.chk_enabled.setChecked(data.get("enabled", True))
        self.chk_enabled.toggled.connect(self.parent_gui.save_config)

        self.txt_name = QLineEdit(data.get("name", "Display Sekunder"))
        self.txt_name.setPlaceholderText("Nama Display...")
        self.txt_name.textChanged.connect(self.parent_gui.save_config)

        self.btn_delete = QPushButton("✕")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.setToolTip("Hapus Layar Sekunder Ini")
        self.btn_delete.clicked.connect(lambda: self.on_remove(self))

        top_layout.addWidget(self.chk_enabled)
        top_layout.addWidget(self.txt_name, stretch=1)
        top_layout.addWidget(self.btn_delete)
        layout.addLayout(top_layout)

        # Baris bawah: Preset & Resolusi/DPI kustom
        bot_layout = QHBoxLayout()
        bot_layout.addWidget(QLabel("Preset:"))
        
        self.combo_preset = QComboBox()
        for label, val in PRESETS:
            self.combo_preset.addItem(label, val)
        
        self.txt_res = QLineEdit(data.get("res", "1200x2133/512"))
        self.txt_res.setPlaceholderText("LEBARxTINGGI/DPI (mis: 1200x2133/512)")
        self.txt_res.textChanged.connect(self.parent_gui.save_config)

        # Cocokkan preset jika ada
        curr_res = self.txt_res.text().strip()
        matched = False
        for idx, (_, val) in enumerate(PRESETS):
            if val and val == curr_res:
                self.combo_preset.setCurrentIndex(idx)
                matched = True
                break
        if not matched:
            self.combo_preset.setCurrentIndex(0)

        self.combo_preset.currentIndexChanged.connect(self.on_preset_changed)

        bot_layout.addWidget(self.combo_preset)
        bot_layout.addWidget(QLabel("Format:"))
        bot_layout.addWidget(self.txt_res, stretch=1)
        layout.addLayout(bot_layout)

        self.setLayout(layout)

    def on_preset_changed(self, idx):
        val = self.combo_preset.itemData(idx)
        if val:
            self.txt_res.setText(val)
        self.parent_gui.save_config()

    def get_data(self):
        return {
            "name": self.txt_name.text().strip(),
            "res": self.txt_res.text().strip(),
            "enabled": self.chk_enabled.isChecked()
        }


class ScrcpyGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.active_processes = []
        self.config = self.load_config()
        self.display_widgets = []
        self.initUI()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(data)
                    return cfg
            except Exception as e:
                print(f"Gagal memuat config: {e}")
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        displays = [w.get_data() for w in self.display_widgets]
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()

        # Update riwayat device jika terisi lengkap
        history = self.config.get("history", [])
        if ip and port:
            full = f"{ip}:{port}"
            if full in history:
                history.remove(full)
            history.insert(0, full)
            history = history[:8]

        self.config = {
            "ip": ip,
            "port": port,
            "history": history,
            "mode": "mirror" if self.radio_mirror.isChecked() else "virtual",
            "mirror_turn_screen_off": self.chk_turn_off_screen.isChecked(),
            "mirror_stay_awake": self.chk_stay_awake.isChecked(),
            "virtual_displays": displays,
            "no_audio": self.chk_no_audio.isChecked(),
            "bitrate": self.combo_bitrate.currentText()
        }

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.log(f"Gagal menyimpan config.json: {e}")

    def initUI(self):
        self.setWindowTitle('Scrcpy & ADB Wi-Fi Manager (Clay Style)')
        self.resize(580, 760)
        self.setStyleSheet(CLAY_STYLESHEET)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 14, 14, 14)
        outer_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(14)

        # ---------------- GROUP 1: KONEKSI ADB WI-FI ----------------
        conn_group = QGroupBox("Koneksi ADB (Wi-Fi Debugging)")
        add_clay_shadow(conn_group)
        conn_layout = QVBoxLayout()
        conn_layout.setSpacing(10)

        # Baris IP & Port + Tombol Paste & Auto IP
        ip_row = QHBoxLayout()
        ip_row.setSpacing(8)

        self.ip_input = QLineEdit(self.config.get("ip", ""))
        self.ip_input.setPlaceholderText("IP (mis: 192.168.1.105)")
        self.ip_input.textChanged.connect(self.on_ip_text_changed)

        self.port_input = QLineEdit(self.config.get("port", "5555"))
        self.port_input.setPlaceholderText("Port")
        self.port_input.setMaximumWidth(90)
        self.port_input.textChanged.connect(self.save_config)

        btn_smart_paste = QPushButton("📋 Paste")
        btn_smart_paste.setToolTip("Otomatis split format IP:Port dari clipboard")
        btn_smart_paste.clicked.connect(self.smart_paste_clipboard)

        btn_detect_ip = QPushButton("🌐 IP Lokal")
        btn_detect_ip.setToolTip("Isi otomatis awalan subnet dari IP komputer")
        btn_detect_ip.clicked.connect(self.auto_fill_subnet)

        ip_row.addWidget(QLabel("IP:"))
        ip_row.addWidget(self.ip_input, stretch=2)
        ip_row.addWidget(QLabel("Port:"))
        ip_row.addWidget(self.port_input)
        ip_row.addWidget(btn_smart_paste)
        ip_row.addWidget(btn_detect_ip)
        conn_layout.addLayout(ip_row)

        # Baris Riwayat & Tombol ADB
        action_row = QHBoxLayout()
        
        self.combo_history = QComboBox()
        self.refresh_history_combo()
        self.combo_history.activated.connect(self.select_from_history)

        self.btn_connect = QPushButton("⚡ Hubungkan ADB")
        self.btn_connect.setObjectName("btnSuccess")
        self.btn_connect.clicked.connect(self.adb_connect)

        self.btn_scan = QPushButton("🔍 Cek Devices")
        self.btn_scan.clicked.connect(self.adb_devices_check)

        action_row.addWidget(QLabel("Riwayat:"))
        action_row.addWidget(self.combo_history, stretch=1)
        action_row.addWidget(self.btn_scan)
        action_row.addWidget(self.btn_connect)
        conn_layout.addLayout(action_row)

        conn_group.setLayout(conn_layout)
        main_layout.addWidget(conn_group)

        # ---------------- GROUP 2: MODE TAMPILAN ----------------
        mode_group = QGroupBox("Pilihan Mode Tampilan")
        add_clay_shadow(mode_group)
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(10)

        radio_row = QHBoxLayout()
        self.mode_group_btns = QButtonGroup(self)
        
        self.radio_mirror = QRadioButton("📱 Layar Primer / Mirror (Copy)")
        self.radio_virtual = QRadioButton("🖥️ Layar Sekunder (Virtual Display)")
        self.mode_group_btns.addButton(self.radio_mirror)
        self.mode_group_btns.addButton(self.radio_virtual)

        if self.config.get("mode") == "virtual":
            self.radio_virtual.setChecked(True)
        else:
            self.radio_mirror.setChecked(True)

        self.radio_mirror.toggled.connect(self.on_mode_switched)
        radio_row.addWidget(self.radio_mirror)
        radio_row.addWidget(self.radio_virtual)
        radio_row.addStretch()
        mode_layout.addLayout(radio_row)

        # Sub-opsi Mirror
        self.mirror_opts_frame = QFrame()
        mirror_opts_layout = QHBoxLayout(self.mirror_opts_frame)
        mirror_opts_layout.setContentsMargins(4, 0, 4, 0)
        self.chk_turn_off_screen = QCheckBox("Matikan Layar HP saat Mirror (--turn-screen-off)")
        self.chk_turn_off_screen.setChecked(self.config.get("mirror_turn_screen_off", False))
        self.chk_turn_off_screen.toggled.connect(self.save_config)

        self.chk_stay_awake = QCheckBox("Cegah HP Tidur (--stay-awake)")
        self.chk_stay_awake.setChecked(self.config.get("mirror_stay_awake", True))
        self.chk_stay_awake.toggled.connect(self.save_config)

        mirror_opts_layout.addWidget(self.chk_turn_off_screen)
        mirror_opts_layout.addWidget(self.chk_stay_awake)
        mirror_opts_layout.addStretch()
        mode_layout.addWidget(self.mirror_opts_frame)

        # Sub-opsi Virtual Displays (Dukungan Multi-Layar)
        self.virtual_opts_frame = QFrame()
        virtual_opts_layout = QVBoxLayout(self.virtual_opts_frame)
        virtual_opts_layout.setContentsMargins(0, 0, 0, 0)
        virtual_opts_layout.setSpacing(8)

        v_top = QHBoxLayout()
        v_lbl = QLabel("Daftar Layar Sekunder yang akan Dibuka:")
        v_lbl.setStyleSheet("font-weight: 600; color: #475569;")
        self.btn_add_display = QPushButton("+ Tambah Layar Sekunder")
        self.btn_add_display.clicked.connect(self.add_new_display_ui)
        v_top.addWidget(v_lbl)
        v_top.addStretch()
        v_top.addWidget(self.btn_add_display)
        virtual_opts_layout.addLayout(v_top)

        self.displays_container = QVBoxLayout()
        self.displays_container.setSpacing(6)
        virtual_opts_layout.addLayout(self.displays_container)

        mode_layout.addWidget(self.virtual_opts_frame)
        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # ---------------- GROUP 3: PENGATURAN GLOBAL ----------------
        global_group = QGroupBox("Pengaturan Streaming Global")
        add_clay_shadow(global_group)
        g_layout = QHBoxLayout()

        self.chk_no_audio = QCheckBox("Matikan Audio (--no-audio)")
        self.chk_no_audio.setChecked(self.config.get("no_audio", True))
        self.chk_no_audio.toggled.connect(self.save_config)

        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems(["2M", "4M", "8M", "12M", "16M", "24M"])
        self.combo_bitrate.setCurrentText(self.config.get("bitrate", "4M"))
        self.combo_bitrate.currentTextChanged.connect(self.save_config)

        g_layout.addWidget(self.chk_no_audio)
        g_layout.addSpacing(20)
        g_layout.addWidget(QLabel("Video Bitrate:"))
        g_layout.addWidget(self.combo_bitrate)
        g_layout.addStretch()
        global_group.setLayout(g_layout)
        main_layout.addWidget(global_group)

        # ---------------- TOMBOL UTAMA START ----------------
        self.btn_start = QPushButton("🚀 Jalankan Scrcpy")
        self.btn_start.setObjectName("btnPrimary")
        add_clay_shadow(self.btn_start, blur=22, offset_y=6, alpha=60)
        self.btn_start.clicked.connect(self.run_scrcpy)
        main_layout.addWidget(self.btn_start)

        # ---------------- LOG TERMINAL ----------------
        main_layout.addWidget(QLabel("Terminal Log Output:"))
        self.log_output = QTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        main_layout.addWidget(self.log_output)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # Inisialisasi daftar display dari config
        self.load_virtual_display_items()
        self.on_mode_switched()

    # ---------------- LOGIC KEMUDAHAN INPUT IP & PORT ----------------
    def on_ip_text_changed(self, text):
        """Mendeteksi jika pengguna mengetik/paste format IP:PORT di kolom IP"""
        clean = text.strip()
        if ":" in clean:
            parts = clean.split(":")
            if len(parts) == 2:
                ip_part, port_part = parts[0].strip(), parts[1].strip()
                self.ip_input.blockSignals(True)
                self.port_input.blockSignals(True)
                self.ip_input.setText(ip_part)
                self.port_input.setText(port_part)
                self.ip_input.blockSignals(False)
                self.port_input.blockSignals(False)
                self.log(f"Auto-split terdeteksi: IP={ip_part}, Port={port_part}")
        self.save_config()

    def smart_paste_clipboard(self):
        """Mengambil teks clipboard dan otomatis memisahkan IP & Port"""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            self.log("Clipboard kosong.")
            return

        # Cek jika ada pola IP:PORT
        match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?', text)
        if match:
            ip = match.group(1)
            port = match.group(2) if match.group(2) else "5555"
            self.ip_input.setText(ip)
            self.port_input.setText(port)
            self.log(f"📋 Smart paste berhasil: {ip}:{port}")
        else:
            self.ip_input.setText(text)
            self.log(f"📋 Teks ditempel ke kolom IP: {text}")
        self.save_config()

    def auto_fill_subnet(self):
        """Mendeteksi IP lokal PC untuk mengisi 3 blok subnet pertama"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split(".")
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}."
            self.ip_input.setText(subnet)
            self.ip_input.setFocus()
            self.log(f"Subnet lokal PC terdeteksi: {subnet}xxx")
        except Exception as e:
            self.log(f"Gagal mendeteksi IP lokal: {e}")

    def refresh_history_combo(self):
        self.combo_history.clear()
        self.combo_history.addItem("-- Pilih Perangkat Tersimpan --")
        for item in self.config.get("history", []):
            self.combo_history.addItem(item)

    def select_from_history(self, idx):
        if idx <= 0:
            return
        selected = self.combo_history.currentText()
        if ":" in selected:
            ip, port = selected.split(":", 1)
            self.ip_input.setText(ip)
            self.port_input.setText(port)
            self.log(f"Memuat dari riwayat: {selected}")
            self.save_config()

    # ---------------- DISPLAY MODES & MULTI-DISPLAY ----------------
    def on_mode_switched(self):
        is_mirror = self.radio_mirror.isChecked()
        self.mirror_opts_frame.setVisible(is_mirror)
        self.virtual_opts_frame.setVisible(not is_mirror)
        self.save_config()

    def load_virtual_display_items(self):
        for w in self.display_widgets:
            w.deleteLater()
        self.display_widgets.clear()

        disp_list = self.config.get("virtual_displays", [])
        if not disp_list:
            disp_list = [{"name": "Display 1", "res": "1200x2133/512", "enabled": True}]

        for item in disp_list:
            self._create_display_widget(item)

    def add_new_display_ui(self):
        idx = len(self.display_widgets) + 1
        new_data = {
            "name": f"Display {idx}",
            "res": "1920x1080/320",
            "enabled": True
        }
        self._create_display_widget(new_data)
        self.save_config()

    def _create_display_widget(self, data):
        w = DisplayItemWidget(data, self, self.remove_display_widget)
        add_clay_shadow(w, blur=10, offset_y=2, alpha=20)
        self.displays_container.addWidget(w)
        self.display_widgets.append(w)

    def remove_display_widget(self, widget):
        if len(self.display_widgets) <= 1:
            QMessageBox.information(self, "Info", "Minimal harus menyisakan 1 pengaturan layar sekunder.")
            return
        self.displays_container.removeWidget(widget)
        self.display_widgets.remove(widget)
        widget.deleteLater()
        self.save_config()

    # ---------------- ADB & SCRCPY EXECUTION ----------------
    def log(self, message):
        self.log_output.append(message)
        scroll_bar = self.log_output.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def adb_connect(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        if not ip or not port:
            QMessageBox.warning(self, "Peringatan", "Harap isi IP dan Port terlebih dahulu!")
            return

        target = f"{ip}:{port}"
        self.log(f"Menghubungkan ADB ke {target}...")
        try:
            res = subprocess.run(["adb", "connect", target], capture_output=True, text=True, timeout=10)
            self.log(res.stdout.strip())
            if res.stderr:
                self.log(f"Error: {res.stderr.strip()}")
            self.refresh_history_combo()
        except Exception as e:
            self.log(f"Gagal menjalankan adb connect: {e}")

    def adb_devices_check(self):
        try:
            res = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, timeout=5)
            self.log("--- Daftar ADB Devices Aktif ---")
            self.log(res.stdout.strip())
        except Exception as e:
            self.log(f"Gagal memeriksa perangkat: {e}")

    def run_scrcpy(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        bitrate = self.combo_bitrate.currentText()
        no_audio = self.chk_no_audio.isChecked()

        base_cmd = ["scrcpy"]
        if ip and port:
            base_cmd.extend(["-s", f"{ip}:{port}"])
        if no_audio:
            base_cmd.append("--no-audio")
        if bitrate:
            base_cmd.append(f"--video-bit-rate={bitrate}")

        is_mirror = self.radio_mirror.isChecked()

        if is_mirror:
            # Mode Primer / Mirror (Copy)
            cmd = list(base_cmd)
            if self.chk_turn_off_screen.isChecked():
                cmd.append("--turn-screen-off")
            if self.chk_stay_awake.isChecked():
                cmd.append("--stay-awake")

            cmd.append("--window-title=Scrcpy (Layar Primer)")
            self.start_process_instance(cmd, "Layar Primer")
        else:
            # Mode Virtual Multi-Display
            active_displays = [w.get_data() for w in self.display_widgets if w.get_data()["enabled"]]
            if not active_displays:
                QMessageBox.warning(self, "Peringatan", "Tidak ada layar sekunder yang dicentang 'Aktif'!")
                return

            self.log(f"Menjalankan {len(active_displays)} layar sekunder...")
            for disp in active_displays:
                cmd = list(base_cmd)
                res = disp.get("res", "").strip()
                name = disp.get("name", "Display Sekunder")

                if res:
                    cmd.append(f"--new-display={res}")
                else:
                    cmd.append("--new-display")

                cmd.append(f"--window-title=Scrcpy - {name}")
                self.start_process_instance(cmd, name)

    def start_process_instance(self, cmd, label):
        proc = QProcess(self)
        self.active_processes.append(proc)

        proc.readyReadStandardOutput.connect(
            lambda p=proc, l=label: self.log(f"[{l}] {p.readAllStandardOutput().data().decode('utf-8', errors='ignore').strip()}")
        )
        proc.readyReadStandardError.connect(
            lambda p=proc, l=label: self.log(f"[{l}] {p.readAllStandardError().data().decode('utf-8', errors='ignore').strip()}")
        )
        proc.finished.connect(
            lambda exitCode, exitStatus, l=label: self.log(f"[{l}] Proses selesai dengan status: {exitCode}")
        )

        cmd_str = " ".join(cmd)
        self.log(f"\nMenjalankan: {cmd_str}")
        proc.start(cmd[0], cmd[1:])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScrcpyGUI()
    window.show()
    sys.exit(app.exec())
