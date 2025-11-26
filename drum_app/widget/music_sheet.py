from dataclasses import dataclass
from typing import Dict, List

import time
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QFont
from PyQt6.QtWidgets import QWidget


@dataclass
class NoteEvent:
    t: float      # time (seconds since start)
    note: int     # MIDI note number


class MusicSheetWidget(QWidget):
    """
    Music-sheet-like view:

    - Horizontal lines per note row (staff-like)
    - Vertical "now" line (playhead)
    - Notes scroll from right to left over time
    """

    def __init__(
        self,
        note_names: Dict[int, str],
        seconds_visible: float = 5.0,
        update_fps: int = 30,
        parent=None,
    ):
        super().__init__(parent)

        self.note_names = note_names          # {midi_note: "Label"}
        self.seconds_visible = seconds_visible
        self.events: List[NoteEvent] = []

        self.start_time = time.time()
        self.current_time = 0.0

        # ✅ Pre-assign rows for all notes so lines render from start
        self.note_rows: Dict[int, int] = {}
        if self.note_names:
            for idx, note in enumerate(sorted(self.note_names.keys())):
                self.note_rows[note] = idx

        # repaint timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / update_fps))

        self.setMinimumHeight(220)

    # --------------------------------------------------
    # Public API: called from GUI thread via signal
    # --------------------------------------------------
    def add_note(self, midi_note: int) -> None:
        # If a note wasn't in NOTE_NAMES but appears later, give it a new row
        if midi_note not in self.note_rows:
            self.note_rows[midi_note] = len(self.note_rows)

        t = time.time() - self.start_time
        self.events.append(NoteEvent(t=t, note=midi_note))
        self._prune_events()
        self.update()

    # --------------------------------------------------
    # Internal time / pruning
    # --------------------------------------------------
    def _tick(self) -> None:
        self.current_time = time.time() - self.start_time
        self._prune_events()
        self.update()

    def _prune_events(self) -> None:
        cutoff = self.current_time - self.seconds_visible
        self.events = [e for e in self.events if e.t >= cutoff]

    # --------------------------------------------------
    # Painting: sheet with lines + playhead
    # --------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # background: white (sheet)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        # if still no notes defined at all, draw a single baseline
        num_rows = max(1, len(self.note_rows))
        row_height = h / num_rows

        # reverse map row -> list of midi notes on that row
        rows_to_notes: Dict[int, List[int]] = {}
        for note, row in self.note_rows.items():
            rows_to_notes.setdefault(row, []).append(note)

        # draw horizontal "staff" lines
        staff_pen = QPen(Qt.GlobalColor.black, 1)
        painter.setPen(staff_pen)

        label_font = QFont()
        label_font.setPointSize(9)
        painter.setFont(label_font)

        left_margin = 60

        for row_idx in range(num_rows):
            y_center = (row_idx + 0.5) * row_height
            painter.drawLine(left_margin, int(y_center), w, int(y_center))

            # label at left
            notes_in_row = rows_to_notes.get(row_idx, [])
            if notes_in_row:
                n = notes_in_row[0]
                label = self.note_names.get(n, f"Note {n}")
                painter.drawText(5, int(y_center + row_height * 0.15), label)

        # vertical "now" line (playhead) at 80% width
        x_now = int(w * 0.8)
        playhead_pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(playhead_pen)
        painter.drawLine(x_now, 0, x_now, h)

        # draw notes as blue dots
        note_brush = QBrush(Qt.GlobalColor.blue)
        painter.setBrush(note_brush)
        painter.setPen(Qt.GlobalColor.blue)

        min_x = left_margin + 10
        max_x = x_now

        for ev in self.events:
            dt = self.current_time - ev.t
            if dt < 0 or dt > self.seconds_visible:
                continue

            frac = dt / self.seconds_visible  # 0 (now) -> 1 (oldest)
            x = max_x - frac * (max_x - min_x)

            row_idx = self.note_rows.get(ev.note, 0)
            y_center = (row_idx + 0.5) * row_height

            radius = min(10, row_height * 0.3)
            painter.drawEllipse(
                int(x - radius),
                int(y_center - radius),
                int(2 * radius),
                int(2 * radius),
            )

        painter.end()
