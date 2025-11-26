import sys
from typing import List

import mido
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QDialog,
    QComboBox,
    QMessageBox,
)

from .widget.music_sheet import MusicSheetWidget
from .constants import NOTE_NAMES
from .midi import USBMIDIReader


# ============================================================
# Port selection dialog
# ============================================================
class PortSelectionDialog(QDialog):
    def __init__(self, ports: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select MIDI Port")
        self.setModal(True)

        self.port_box = QComboBox()
        self.port_box.addItems(ports)

        ok_button = QPushButton("Start")
        ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Select MIDI Input Device:"))
        layout.addWidget(self.port_box)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def selected_port(self) -> str:
        return self.port_box.currentText()


# ============================================================
# Main GUI window
# ============================================================
class DrumApp(QWidget):
    # note, velocity
    note_received = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Drum Trainer")
        self.reader: USBMIDIReader | None = None

        # --------------------------------------------------
        # Widgets
        # --------------------------------------------------
        self.status_label = QLabel("🎧 Starting Drum Trainer...\nDetecting MIDI ports...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.port_label = QLabel("")
        self.port_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Notation sheet widget
        self.sheet = MusicSheetWidget(note_names=NOTE_NAMES)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)

        # --------------------------------------------------
        # Layout
        # --------------------------------------------------
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.port_label)
        layout.addWidget(self.sheet)
        layout.addWidget(quit_button)

        self.setLayout(layout)

        # Connect MIDI → sheet
        self.note_received.connect(self.sheet.add_midi_hit)

        # Show startup, then ask for port
        QTimer.singleShot(800, self.show_port_dialog)

    # ============================================================
    # MIDI port selection
    # ============================================================
    def show_port_dialog(self):
        ports = mido.get_input_names()

        if not ports:
            QMessageBox.warning(
                self,
                "No MIDI Ports",
                "No MIDI input ports found.\n"
                "Please connect your drum kit / MIDI device and restart the app.",
            )
            self.status_label.setText("❌ No MIDI ports found.")
            return

        dialog = PortSelectionDialog(ports, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            port = dialog.selected_port()
            self.start_reader(port)
        else:
            self.status_label.setText("Cancelled port selection.")

    # ============================================================
    # Start reader (after user selects port)
    # ============================================================
    def start_reader(self, port_name: str):

        # Stop old reader if any
        if self.reader is not None:
            self.reader.stop()

        # Handler runs in MIDI thread: emit signal back to GUI thread
        def handle_msg(msg):
            if msg.type == "note_on" and msg.velocity > 0:
                self.note_received.emit(msg.note, msg.velocity)

        # Don't auto-detect – we already know the port
        self.reader = USBMIDIReader(
            message_handler=handle_msg,
            auto_start=False,
            port_keyword=None,
        )

        self.reader.start(port_name)

        self.status_label.setText("✅ Reading MIDI events")
        self.port_label.setText(f"Connected to: <b>{port_name}</b>")

    # ============================================================
    # Close cleanup
    # ============================================================
    def closeEvent(self, event):
        if self.reader is not None:
            self.reader.stop()
        event.accept()


# ============================================================
# Entry point
# ============================================================
def main():
    app = QApplication(sys.argv)
    window = DrumApp()
    window.resize(900, 500)
    window.show()
    sys.exit(app.exec())


