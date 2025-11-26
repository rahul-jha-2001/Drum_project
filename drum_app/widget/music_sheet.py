from dataclasses import dataclass
from typing import Dict, List, Tuple

import time
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QPen, QFont
from PyQt6.QtWidgets import QWidget

from ..DrumNotationMapper import DrumNotationMapper


@dataclass
class VisualNote:
    t: float                  # time (seconds since start)
    midi_note: int
    notehead: str
    position: str
    articulation: str


class MusicSheetWidget(QWidget):
    """
    Drum music sheet view:

    - Fixed 5-line staff
    - Vertical "now" playhead
    - Notes drawn as notation symbols (x, o, ♩) on the staff
    """

    def __init__(
        self,
        note_names: Dict[int, str],
        seconds_visible: float = 5.0,
        update_fps: int = 30,
        parent=None,
    ):
        super().__init__(parent)

        self.note_names = note_names
        self.seconds_visible = seconds_visible
        self.events: List[VisualNote] = []

        self.start_time = time.time()
        self.current_time = 0.0

        # Drum notation mapper
        self.mapper = DrumNotationMapper()

        # Invert DRUM_NOTATION_TO_MIDI: midi_note -> (notehead, position)
        self.midi_to_notation: Dict[int, Tuple[str, str]] = {}
        for (notehead, position), midi_note in self.mapper.DRUM_NOTATION_TO_MIDI.items():
            if midi_note not in self.midi_to_notation:
                self.midi_to_notation[midi_note] = (notehead, position)

        # Staff step mapping for vertical placement
        self.position_to_step = {
            "below_bottom_line": -1,
            "bottom_line": 0,
            "second_space": 1,
            "middle_line": 2,
            "third_space": 3,
            "top_line": 4,
            "top_space": 5,
            "above_top_line": 6,
            "above_top_line_crash": 6,
            "space_above_top_line": 7,
            "above_staff": 8,
        }

        # Timer to update animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(int(1000 / update_fps))

        self.setMinimumHeight(260)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def add_midi_hit(self, midi_note: int, velocity: int) -> None:
        if midi_note in self.midi_to_notation:
            notehead, position = self.midi_to_notation[midi_note]
        else:
            notehead, position = "normal", "middle_line"

        if velocity <= 40:
            articulation = "ghost"
        elif velocity >= 105:
            articulation = "accent"
        else:
            articulation = "normal"

        t = time.time() - self.start_time
        self.events.append(
            VisualNote(
                t=t,
                midi_note=midi_note,
                notehead=notehead,
                position=position,
                articulation=articulation,
            )
        )
        self._prune_events()
        self.update()

    def add_note(self, midi_note: int) -> None:
        self.add_midi_hit(midi_note, velocity=80)

    # --------------------------------------------------
    # Time / pruning
    # --------------------------------------------------
    def _tick(self) -> None:
        self.current_time = time.time() - self.start_time
        self._prune_events()
        self.update()

    def _prune_events(self) -> None:
        cutoff = self.current_time - self.seconds_visible
        self.events = [e for e in self.events if e.t >= cutoff]

    # --------------------------------------------------
    # Geometry helpers
    # --------------------------------------------------
    def _staff_geometry(self, w: int, h: int):
        """
        Returns (left_margin, bottom_y, line_gap, top_limit, bottom_limit).

        Staff is centered vertically with padding so top/bottom symbols don't clip.
        """
        left_margin = 60

        # vertical padding
        top_margin = 30
        bottom_margin = 30

        # define staff region between these
        top_staff_y = top_margin + 20
        bottom_staff_y = h - bottom_margin

        staff_height = bottom_staff_y - top_staff_y
        if staff_height <= 0:  # fallback
            staff_height = max(h * 0.5, 50)
            bottom_staff_y = h - bottom_margin
            top_staff_y = bottom_staff_y - staff_height

        line_gap = staff_height / 4  # 4 gaps for 5 lines

        # define safe drawing band for symbol centers
        top_limit = top_margin
        bottom_limit = h - bottom_margin

        return left_margin, bottom_staff_y, line_gap, top_limit, bottom_limit

    def _y_for_position(
        self,
        position: str,
        bottom_y: float,
        line_gap: float,
        top_limit: float,
        bottom_limit: float,
    ) -> float:
        step = self.position_to_step.get(position, 2)  # default middle line
        y = bottom_y - step * line_gap

        # clamp so glyph centers don't go outside widget
        y = max(top_limit, min(bottom_limit, y))
        return y

    def _symbol_for_notehead(self, notehead: str) -> str:
        if notehead in {"x", "+", "X"}:
            return "x"
        if notehead in {"o", "O"}:
            return "o"
        return "♩"

    def _color_for_articulation(self, articulation: str):
        if articulation == "ghost":
            return Qt.GlobalColor.darkGray
        if articulation == "accent":
            return Qt.GlobalColor.darkRed
        return Qt.GlobalColor.blue

    # --------------------------------------------------
    # Painting
    # --------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # background
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        left_margin, bottom_y, line_gap, top_limit, bottom_limit = self._staff_geometry(
            w, h
        )

        # --- staff lines (5) ---
        staff_pen = QPen(Qt.GlobalColor.black, 1)
        painter.setPen(staff_pen)

        for i in range(5):
            y = bottom_y - i * line_gap
            painter.drawLine(left_margin, int(y), w - 10, int(y))

        # --- playhead --
        x_now = int(w * 0.8)
        playhead_pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(playhead_pen)
        painter.drawLine(x_now, 0, x_now, h)

        # --- notes as notation glyphs ---
        min_x = left_margin + 10
        max_x = x_now

        note_font = QFont()
        note_font.setPointSize(16)  # slightly smaller to avoid clipping
        painter.setFont(note_font)

        for ev in self.events:
            dt = self.current_time - ev.t
            if dt < 0 or dt > self.seconds_visible:
                continue

            frac = dt / self.seconds_visible  # 0 (now) -> 1 (oldest in window)
            x = max_x - frac * (max_x - min_x)

            y_center = self._y_for_position(
                ev.position, bottom_y, line_gap, top_limit, bottom_limit
            )

            symbol = self._symbol_for_notehead(ev.notehead)
            painter.setPen(self._color_for_articulation(ev.articulation))

            text_w = 24
            text_h = 24
            painter.drawText(
                int(x - text_w / 2),
                int(y_center - text_h / 2),
                text_w,
                text_h,
                Qt.AlignmentFlag.AlignCenter,
                symbol,
            )

        painter.end()