from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class NotationEvent:
    """
    Represents a single drum notation event on the staff.
    You can construct this from whatever your GUI / parser gives you.
    """
    notehead: str          # e.g. "x", "o", "normal", "accent"
    position: str          # e.g. "top_space", "middle_line", "below_bottom_line"
    articulation: str = "normal"  # "normal", "ghost", "accent", "rimshot"
    dynamic: Optional[str] = None  # "pp", "p", "mp", "mf", "f", "ff"


class DrumNotationMapper:
    """
    Maps drum notation (symbol + staff position) to:
      - MIDI note number (which drum sound)
      - MIDI velocity (how hard it is played)
    """

    # --- 1. General MIDI drum map: note -> name (for reference / debugging) ---
    GM_DRUM_MAP = {
        35: "Acoustic Bass Drum",
        36: "Bass Drum 1",
        37: "Side Stick",
        38: "Acoustic Snare",
        39: "Hand Clap",
        40: "Electric Snare",
        41: "Low Floor Tom",
        42: "Closed Hi-Hat",
        43: "High Floor Tom",
        44: "Pedal Hi-Hat",
        45: "Low Tom",
        46: "Open Hi-Hat",
        47: "Low-Mid Tom",
        48: "Hi-Mid Tom",
        49: "Crash Cymbal 1",
        50: "High Tom",
        51: "Ride Cymbal 1",
        52: "Chinese Cymbal",
        53: "Ride Bell",
        57: "Crash Cymbal 2",
    }

    # --- 2. Notation (notehead + position) -> MIDI note number ---
    # Positions are symbolic; adapt them to how *your* renderer names them.
    DRUM_NOTATION_TO_MIDI = {
        # Hi-hats
        ("x", "top_space"): 42,              # Closed hi-hat
        ("+", "top_space"): 42,              # Explicit closed hi-hat
        ("x", "above_top_line"): 46,         # Open hi-hat
        ("O", "above_top_line"): 46,         # Explicit open hi-hat
        ("x", "above_staff"): 44,            # Hi-hat pedal

        # Snare (middle line)
        ("normal", "middle_line"): 38,
        ("accent", "middle_line"): 38,
        ("o", "middle_line"): 38,            # Ghost note on snare

        # Kick (bass drum)
        ("normal", "below_bottom_line"): 36,

        # Toms
        ("normal", "second_space"): 48,      # High tom
        ("normal", "third_space"): 47,       # Mid tom
        ("normal", "fourth_space"): 45,      # Low tom
        ("normal", "bottom_line"): 43,       # Floor tom

        # Cymbals
        ("x", "above_top_line_crash"): 49,   # Crash (if you want a separate position name)
        ("x", "top_line"): 51,               # Ride
        ("x", "space_above_top_line"): 53,   # Ride bell
    }

    # --- 3. Articulation -> base velocity ---
    VELOCITY_MAP = {
        "ghost": 30,
        "normal": 80,
        "accent": 110,
        "rimshot": 120,
    }

    # --- 4. Dynamic marking -> multiplier on top of articulation velocity ---
    DYNAMIC_MULTIPLIER = {
        "pp": 0.5,
        "p": 0.7,
        "mp": 0.85,
        "mf": 1.0,
        "f": 1.15,
        "ff": 1.3,
    }

    def get_midi_note(self, notehead: str, position: str) -> Optional[int]:
        """
        Map (notehead, staff position) -> MIDI note number.
        Returns None if not found.
        """
        key = (notehead, position)
        if key in self.DRUM_NOTATION_TO_MIDI:
            return self.DRUM_NOTATION_TO_MIDI[key]

        # Fallbacks: treat unknown notehead as "normal"
        fallback_key = ("normal", position)
        return self.DRUM_NOTATION_TO_MIDI.get(fallback_key)

    def get_velocity(self, articulation: str = "normal", dynamic: Optional[str] = None) -> int:
        """
        Compute MIDI velocity from articulation + dynamic marking.
        Clamps result to [1, 127].
        """
        base_vel = self.VELOCITY_MAP.get(articulation, self.VELOCITY_MAP["normal"])

        if dynamic:
            mult = self.DYNAMIC_MULTIPLIER.get(dynamic, 1.0)
        else:
            mult = 1.0

        vel = int(base_vel * mult)
        vel = max(1, min(127, vel))
        return vel

    def map_event(self, event: NotationEvent) -> Optional[Tuple[int, int]]:
        """
        Main entry point:
        Takes a NotationEvent and returns (midi_note, velocity),
        or None if the event cannot be mapped.
        """
        midi_note = self.get_midi_note(event.notehead, event.position)
        if midi_note is None:
            # Unknown mapping; you can log or raise here instead
            return None

        velocity = self.get_velocity(event.articulation, event.dynamic)
        return midi_note, velocity

    # Optional: helper for debugging / logs
    def describe_event(self, event: NotationEvent) -> str:
        """
        Human-readable description useful for logging.
        """
        mapped = self.map_event(event)
        if mapped is None:
            return f"Unmapped notation: {event}"

        midi_note, velocity = mapped
        drum_name = self.GM_DRUM_MAP.get(midi_note, "Unknown Drum")
        return (f"Notation {event.notehead}@{event.position} "
                f"(articulation={event.articulation}, dynamic={event.dynamic}) "
                f"-> MIDI {midi_note} ({drum_name}), vel={velocity}")
# Example usage: