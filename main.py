import sys
import json
import os
import re
import socket
import subprocess
import shutil
import platform
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QCheckBox, 
    QComboBox, QTextEdit, QMessageBox,
    QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QColor, QFont, QCursor

CONFIG_FILE = "config.json"
IS_WINDOWS = platform.system() == "Windows"

def get_base_dir():
    """Mendapatkan direktori dasar (folder temporary PyInstaller jika dibungkus, atau folder skrip)"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_binary_path(name):
    """
    Mencari lokasi binary 'adb' atau 'scrcpy':
    1. Di bundle folder PyInstaller (sys._MEIPASS) jika dibungkus single-file EXE.
    2. Di direktori yang sama dengan aplikasi.
    3. Di PATH sistem operasi.
    """
    exts = [".exe", ".cmd", ".bat"] if IS_WINDOWS else [""]
    base_dir = get_base_dir()

    # 1. Cek di base dir (PyInstaller bundle / lokal)
    for ext in exts:
        candidate = os.path.join(base_dir, f"{name}{ext}")
        if os.path.isfile(candidate):
            return candidate

    # 2. Cek di PATH sistem
    found = shutil.which(name)
    if found:
        return found

    return f"{name}.exe" if IS_WINDOWS else name

def setup_environment():
    """
    Menyiapkan environment variables penting:
    - Jika dibungkus PyInstaller di Windows, pastikan scrcpy tahu di mana scrcpy-server berada.
    """
    base_dir = get_base_dir()
    server_path = os.path.join(base_dir, "scrcpy-server")
    if os.path.isfile(server_path):
        os.environ["SCRCPY_SERVER_PATH"] = server_path

def get_subprocess_kwargs():
    """Mencegah jendela CMD/konsol hitam berkedip di Windows saat eksekusi subprocess."""
    kwargs = {}
    if IS_WINDOWS:
        # Gunakan flag CREATE_NO_WINDOW (0x08000000)
        kwargs["creationflags"] = 0x08000000
    return kwargs

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
            "res": "1080x1920/320",
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
/* Global Window Styling */
QWidget {
    background-color: #EBF0F7;
    font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
    color: #334155;
    font-size: 13px;
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
    min-height: 28px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Clay Cards */
QFrame.clayCard {
    background-color: #FFFFFF;
    border-radius: 20px;
    border: 1px solid #F1F5F9;
}

/* Header Text di dalam Card */
QLabel.cardTitle {
    font-size: 14px;
    font-weight: 700;
    color: #1E293B;
    background: transparent;
}

QLabel.fieldLabel {
    font-size: 12px;
    font-weight: 600;
    color: #64748B;
    background: transparent;
}

/* Soft Inset Input Fields */
QLineEdit {
    background-color: #F1F5F9;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 7px 12px;
    color: #0F172A;
    font-weight: 500;
}
QLineEdit:focus {
    background-color: #FFFFFF;
    border: 2px solid #6366F1;
}

/* Styling Dropdown QComboBox */
QComboBox {
    background-color: #F1F5F9;
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 6px 12px;
    color: #0F172A;
    font-weight: 500;
}
QComboBox:focus, QComboBox:hover {
    border: 2px solid #6366F1;
    background-color: #FFFFFF;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
    padding-right: 4px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #64748B;
    width: 0;
    height: 0;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    selection-background-color: #EEF2FF;
    selection-color: #4F46E5;
    padding: 6px;
    outline: none;
}

/* Tombol Empuk Claymorphic */
QPushButton {
    background-color: #F8FAFC;
    color: #334155;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #EEF2FF;
    color: #4F46E5;
    border-color: #C7D2FE;
}
QPushButton:pressed {
    background-color: #E0E7FF;
    padding-top: 10px;
}

/* Tombol Connect ADB (Hijau Soft) */
QPushButton#btnConnect {
    background-color: #10B981;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 8px 16px;
    font-weight: 700;
}
QPushButton#btnConnect:hover {
    background-color: #059669;
}
QPushButton#btnConnect:pressed {
    background-color: #047857;
    padding-top: 10px;
}

/* Tombol Tambah Display */
QPushButton#btnAddDisplay {
    background-color: #EEF2FF;
    color: #4F46E5;
    border: 1.5px dashed #A5B4FC;
    border-radius: 12px;
    padding: 6px 14px;
    font-weight: 600;
}
QPushButton#btnAddDisplay:hover {
    background-color: #E0E7FF;
    border-style: solid;
}

/* Tombol Hapus Display (Merah Soft) */
QPushButton#btnDeleteDisplay {
    background-color: #FEE2E2;
    color: #DC2626;
    border: none;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: bold;
    font-size: 11px;
}
QPushButton#btnDeleteDisplay:hover {
    background-color: #FCA5A5;
    color: #991B1B;
}

/* Tombol Utama Jalankan Scrcpy */
QPushButton#btnStart {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
    color: #FFFFFF;
    border: none;
    border-radius: 18px;
    padding: 14px;
    font-weight: 800;
    font-size: 15px;
    letter-spacing: 0.5px;
}
QPushButton#btnStart:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4F46E5, stop:1 #4338CA);
}
QPushButton#btnStart:pressed {
    background-color: #3730A3;
    padding-top: 16px;
}

/* Segmented Capsule Switcher */
QFrame#pillSwitchContainer {
    background-color: #F1F5F9;
    border-radius: 16px;
    padding: 4px;
    border: 1px solid #E2E8F0;
}
QPushButton.pillSegment {
    background-color: transparent;
    border: none;
    border-radius: 12px;
    padding: 8px 18px;
    font-weight: 600;
    color: #64748B;
}
QPushButton.pillSegment:hover {
    color: #1E293B;
}
QPushButton.pillSegmentActive {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 8px 18px;
    font-weight: 700;
    color: #4F46E5;
}

/* Checkbox empuk */
QCheckBox {
    font-size: 13px;
    spacing: 8px;
    color: #334155;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 2px solid #CBD5E1;
    background-color: #F8FAFC;
}
QCheckBox::indicator:hover {
    border-color: #818CF8;
}
QCheckBox::indicator:checked {
    background-color: #6366F1;
    border-color: #6366F1;
}

/* Inner Display Item Card */
QFrame.innerCard {
    background-color: #F8FAFC;
    border-radius: 14px;
    border: 1px solid #E2E8F0;
    padding: 8px 12px;
}

/* Terminal Log View */
QTextEdit#logOutput {
    background-color: #0F172A;
    color: #38BDF8;
    border-radius: 16px;
    border: 1px solid #1E293B;
    padding: 12px;
    font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
    font-size: 11.5px;
}
"""

def add_clay_shadow(widget, blur=18, offset_y=4, alpha=22):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset_y)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)

class DisplayItemWidget(QFrame):
    """Card item untuk masing-masing Layar Sekunder"""
    def __init__(self, data, parent_gui, on_remove):
        super().__init__()
        self.parent_gui = parent_gui
        self.on_remove = on_remove
        self.setProperty("class", "innerCard")
        self.initUI(data)

    def initUI(self, data):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Baris 1: Status Aktif, Nama Display, Tombol Hapus
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.chk_enabled = QCheckBox("Aktif")
        self.chk_enabled.setChecked(data.get("enabled", True))
        self.chk_enabled.toggled.connect(self.parent_gui.save_config)

        self.txt_name = QLineEdit(data.get("name", "Display Sekunder"))
        self.txt_name.setPlaceholderText("Nama Display (mis: Tablet Vertikal)")
        self.txt_name.textChanged.connect(self.parent_gui.save_config)

        self.btn_delete = QPushButton("✕ Hapus")
        self.btn_delete.setObjectName("btnDeleteDisplay")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.clicked.connect(lambda: self.on_remove(self))

        top_row.addWidget(self.chk_enabled)
        top_row.addWidget(self.txt_name, stretch=1)
        top_row.addWidget(self.btn_delete)
        layout.addLayout(top_row)

        # Baris 2: Preset Cepat & Input Ukuran
        bot_row = QHBoxLayout()
        bot_row.setSpacing(8)

        lbl_preset = QLabel("Preset:")
        lbl_preset.setProperty("class", "fieldLabel")
        self.combo_preset = QComboBox()
        for label, val in PRESETS:
            self.combo_preset.addItem(label, val)

        lbl_res = QLabel("Format:")
        lbl_res.setProperty("class", "fieldLabel")
        self.txt_res = QLineEdit(data.get("res", "1080x1920/320"))
        self.txt_res.setPlaceholderText("PxL/DPI mis: 1200x2133/512")
        self.txt_res.textChanged.connect(self.parent_gui.save_config)

        # Cek kesesuaian preset
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

        bot_row.addWidget(lbl_preset)
        bot_row.addWidget(self.combo_preset, stretch=2)
        bot_row.addWidget(lbl_res)
        bot_row.addWidget(self.txt_res, stretch=2)
        layout.addLayout(bot_row)

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
            "mode": "mirror" if self.current_mode == "mirror" else "virtual",
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
        self.setWindowTitle('Scrcpy & ADB Wi-Fi Controller (Clay Edition)')
        self.resize(620, 840)
        self.setMinimumWidth(560)
        self.setStyleSheet(CLAY_STYLESHEET)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 14, 14, 14)
        outer_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(14)

        # ================= CARD 1: KONEKSI ADB WI-FI =================
        card_conn = QFrame()
        card_conn.setProperty("class", "clayCard")
        add_clay_shadow(card_conn, blur=18, offset_y=4, alpha=24)
        card_conn_layout = QVBoxLayout(card_conn)
        card_conn_layout.setContentsMargins(16, 16, 16, 16)
        card_conn_layout.setSpacing(12)

        title_conn = QLabel("⚡ Koneksi ADB (Wi-Fi Debugging)")
        title_conn.setProperty("class", "cardTitle")
        card_conn_layout.addWidget(title_conn)

        # Baris IP & Port + Tombol Smart Paste & IP Lokal
        ip_row = QHBoxLayout()
        ip_row.setSpacing(8)

        lbl_ip = QLabel("IP:")
        lbl_ip.setProperty("class", "fieldLabel")
        self.ip_input = QLineEdit(self.config.get("ip", ""))
        self.ip_input.setPlaceholderText("misal: 192.168.1.100")
        self.ip_input.textChanged.connect(self.on_ip_text_changed)

        lbl_port = QLabel("Port:")
        lbl_port.setProperty("class", "fieldLabel")
        self.port_input = QLineEdit(self.config.get("port", "5555"))
        self.port_input.setPlaceholderText("Port")
        self.port_input.setFixedWidth(85)
        self.port_input.textChanged.connect(self.save_config)

        btn_smart_paste = QPushButton("📋 Paste")
        btn_smart_paste.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_smart_paste.setToolTip("Auto-split format IP:Port dari clipboard")
        btn_smart_paste.clicked.connect(self.smart_paste_clipboard)

        btn_detect_ip = QPushButton("🌐 IP Lokal")
        btn_detect_ip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_detect_ip.setToolTip("Auto-fill 3 blok subnet komputer")
        btn_detect_ip.clicked.connect(self.auto_fill_subnet)

        ip_row.addWidget(lbl_ip)
        ip_row.addWidget(self.ip_input, stretch=3)
        ip_row.addWidget(lbl_port)
        ip_row.addWidget(self.port_input)
        ip_row.addWidget(btn_smart_paste)
        ip_row.addWidget(btn_detect_ip)
        card_conn_layout.addLayout(ip_row)

        # Baris Riwayat & Aksi ADB
        act_row = QHBoxLayout()
        act_row.setSpacing(8)

        lbl_hist = QLabel("Riwayat:")
        lbl_hist.setProperty("class", "fieldLabel")
        self.combo_history = QComboBox()
        self.refresh_history_combo()
        self.combo_history.activated.connect(self.select_from_history)

        self.btn_scan = QPushButton("🔍 Cek Devices")
        self.btn_scan.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_scan.clicked.connect(self.adb_devices_check)

        self.btn_connect = QPushButton("Connect ADB")
        self.btn_connect.setObjectName("btnConnect")
        self.btn_connect.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_connect.clicked.connect(self.adb_connect)

        act_row.addWidget(lbl_hist)
        act_row.addWidget(self.combo_history, stretch=1)
        act_row.addWidget(self.btn_scan)
        act_row.addWidget(self.btn_connect)
        card_conn_layout.addLayout(act_row)

        main_layout.addWidget(card_conn)

        # ================= CARD 2: PILIHAN MODE TAMPILAN =================
        card_mode = QFrame()
        card_mode.setProperty("class", "clayCard")
        add_clay_shadow(card_mode, blur=18, offset_y=4, alpha=24)
        card_mode_layout = QVBoxLayout(card_mode)
        card_mode_layout.setContentsMargins(16, 16, 16, 16)
        card_mode_layout.setSpacing(14)

        title_mode = QLabel("🖥️ Pengaturan Tampilan & Layar")
        title_mode.setProperty("class", "cardTitle")
        card_mode_layout.addWidget(title_mode)

        # Segmented Pill Switcher
        pill_frame = QFrame()
        pill_frame.setObjectName("pillSwitchContainer")
        pill_layout = QHBoxLayout(pill_frame)
        pill_layout.setContentsMargins(4, 4, 4, 4)
        pill_layout.setSpacing(4)

        self.btn_tab_mirror = QPushButton("📱 Layar Primer / Mirror (Copy)")
        self.btn_tab_virtual = QPushButton("🖥️ Layar Sekunder (Virtual Display)")
        self.btn_tab_mirror.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tab_virtual.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.current_mode = self.config.get("mode", "mirror")
        self.btn_tab_mirror.clicked.connect(lambda: self.switch_mode_ui("mirror"))
        self.btn_tab_virtual.clicked.connect(lambda: self.switch_mode_ui("virtual"))

        pill_layout.addWidget(self.btn_tab_mirror, stretch=1)
        pill_layout.addWidget(self.btn_tab_virtual, stretch=1)
        card_mode_layout.addWidget(pill_frame)

        # Sub-opsi Mirror
        self.mirror_panel = QFrame()
        m_layout = QHBoxLayout(self.mirror_panel)
        m_layout.setContentsMargins(4, 4, 4, 4)
        m_layout.setSpacing(16)

        self.chk_turn_off_screen = QCheckBox("Matikan Layar Fisik HP (--turn-screen-off)")
        self.chk_turn_off_screen.setChecked(self.config.get("mirror_turn_screen_off", False))
        self.chk_turn_off_screen.toggled.connect(self.save_config)

        self.chk_stay_awake = QCheckBox("Cegah HP Tidur (--stay-awake)")
        self.chk_stay_awake.setChecked(self.config.get("mirror_stay_awake", True))
        self.chk_stay_awake.toggled.connect(self.save_config)

        m_layout.addWidget(self.chk_turn_off_screen)
        m_layout.addWidget(self.chk_stay_awake)
        m_layout.addStretch()
        card_mode_layout.addWidget(self.mirror_panel)

        # Sub-opsi Virtual Multi-Display
        self.virtual_panel = QFrame()
        v_layout = QVBoxLayout(self.virtual_panel)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)

        v_head = QHBoxLayout()
        v_head_lbl = QLabel("Daftar Layar Virtual yang akan Dibuka:")
        v_head_lbl.setProperty("class", "fieldLabel")
        self.btn_add_display = QPushButton("+ Tambah Layar")
        self.btn_add_display.setObjectName("btnAddDisplay")
        self.btn_add_display.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_display.clicked.connect(self.add_new_display_ui)

        v_head.addWidget(v_head_lbl)
        v_head.addStretch()
        v_head.addWidget(self.btn_add_display)
        v_layout.addLayout(v_head)

        self.displays_container = QVBoxLayout()
        self.displays_container.setSpacing(8)
        v_layout.addLayout(self.displays_container)

        card_mode_layout.addWidget(self.virtual_panel)
        main_layout.addWidget(card_mode)

        # ================= CARD 3: PENGATURAN GLOBAL =================
        card_global = QFrame()
        card_global.setProperty("class", "clayCard")
        add_clay_shadow(card_global, blur=18, offset_y=4, alpha=24)
        card_global_layout = QHBoxLayout(card_global)
        card_global_layout.setContentsMargins(16, 12, 16, 12)
        card_global_layout.setSpacing(16)

        self.chk_no_audio = QCheckBox("Matikan Audio (--no-audio)")
        self.chk_no_audio.setChecked(self.config.get("no_audio", True))
        self.chk_no_audio.toggled.connect(self.save_config)

        lbl_br = QLabel("Video Bitrate:")
        lbl_br.setProperty("class", "fieldLabel")
        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems(["2M", "4M", "8M", "12M", "16M", "24M"])
        self.combo_bitrate.setCurrentText(self.config.get("bitrate", "4M"))
        self.combo_bitrate.currentTextChanged.connect(self.save_config)

        card_global_layout.addWidget(self.chk_no_audio)
        card_global_layout.addStretch()
        card_global_layout.addWidget(lbl_br)
        card_global_layout.addWidget(self.combo_bitrate)
        main_layout.addWidget(card_global)

        # ================= TOMBOL UTAMA START =================
        self.btn_start = QPushButton("🚀  JALANKAN SCRCPY")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_clay_shadow(self.btn_start, blur=24, offset_y=6, alpha=70)
        self.btn_start.clicked.connect(self.run_scrcpy)
        main_layout.addWidget(self.btn_start)

        # ================= LOG TERMINAL =================
        log_label = QLabel("Output Log Terminal:")
        log_label.setProperty("class", "fieldLabel")
        main_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(130)
        main_layout.addWidget(self.log_output)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # Inisialisasi tampilan
        self.load_virtual_display_items()
        self.switch_mode_ui(self.current_mode)

    # ---------------- INTERAKSI MODE TAMPILAN ----------------
    def switch_mode_ui(self, mode):
        self.current_mode = mode
        if mode == "mirror":
            self.btn_tab_mirror.setProperty("class", "pillSegmentActive")
            self.btn_tab_virtual.setProperty("class", "pillSegment")
            self.mirror_panel.setVisible(True)
            self.virtual_panel.setVisible(False)
        else:
            self.btn_tab_mirror.setProperty("class", "pillSegment")
            self.btn_tab_virtual.setProperty("class", "pillSegmentActive")
            self.mirror_panel.setVisible(False)
            self.virtual_panel.setVisible(True)

        self.btn_tab_mirror.style().unpolish(self.btn_tab_mirror)
        self.btn_tab_mirror.style().polish(self.btn_tab_mirror)
        self.btn_tab_virtual.style().unpolish(self.btn_tab_virtual)
        self.btn_tab_virtual.style().polish(self.btn_tab_virtual)
        self.save_config()

    def load_virtual_display_items(self):
        for w in self.display_widgets:
            w.deleteLater()
        self.display_widgets.clear()

        disp_list = self.config.get("virtual_displays", [])
        if not disp_list:
            disp_list = [{"name": "Display 1 (Vertical)", "res": "1080x1920/320", "enabled": True}]

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
        add_clay_shadow(w, blur=8, offset_y=2, alpha=15)
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

    # ---------------- INTERAKSI IP & PORT ----------------
    def on_ip_text_changed(self, text):
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
                self.log(f"Auto-split format terdeteksi: IP={ip_part}, Port={port_part}")
        self.save_config()

    def smart_paste_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            self.log("Clipboard kosong.")
            return

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
        adb_bin = get_binary_path("adb")
        self.log(f"Menghubungkan ADB ke {target}...")
        try:
            res = subprocess.run(
                [adb_bin, "connect", target], 
                capture_output=True, 
                text=True, 
                timeout=10,
                **get_subprocess_kwargs()
            )
            self.log(res.stdout.strip())
            if res.stderr:
                self.log(f"Error: {res.stderr.strip()}")
            self.refresh_history_combo()
        except Exception as e:
            self.log(f"Gagal menjalankan adb connect: {e}")

    def adb_devices_check(self):
        adb_bin = get_binary_path("adb")
        try:
            res = subprocess.run(
                [adb_bin, "devices", "-l"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                **get_subprocess_kwargs()
            )
            self.log("--- Daftar ADB Devices Aktif ---")
            self.log(res.stdout.strip())
        except Exception as e:
            self.log(f"Gagal memeriksa perangkat: {e}")

    def run_scrcpy(self):
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        bitrate = self.combo_bitrate.currentText()
        no_audio = self.chk_no_audio.isChecked()

        scrcpy_bin = get_binary_path("scrcpy")
        base_cmd = [scrcpy_bin]
        if ip and port:
            base_cmd.extend(["-s", f"{ip}:{port}"])
        if no_audio:
            base_cmd.append("--no-audio")
        if bitrate:
            base_cmd.append(f"--video-bit-rate={bitrate}")

        if self.current_mode == "mirror":
            cmd = list(base_cmd)
            if self.chk_turn_off_screen.isChecked():
                cmd.append("--turn-screen-off")
            if self.chk_stay_awake.isChecked():
                cmd.append("--stay-awake")

            cmd.append("--window-title=Scrcpy (Layar Primer)")
            self.start_process_instance(cmd, "Layar Primer")
        else:
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
            lambda exitCode, exitStatus, l=label: self.log(f"[{l}] Proses selesai (code: {exitCode})")
        )

        cmd_str = " ".join(cmd)
        self.log(f"\n🚀 Menjalankan: {cmd_str}")
        proc.start(cmd[0], cmd[1:])


if __name__ == '__main__':
    setup_environment()
    app = QApplication(sys.argv)
    window = ScrcpyGUI()
    window.show()
    sys.exit(app.exec())
