"""Helper utilities for discovering connected MIDI ports."""

from __future__ import annotations

from typing import List

import mido


def get_input_ports() -> List[str]:
    """Return all detected MIDI input port names."""

    return list(mido.get_input_names())


def get_output_ports() -> List[str]:
    """Return all detected MIDI output port names."""

    return list(mido.get_output_names())


def format_port_listing() -> str:
    """Build a formatted string that lists MIDI input/output ports."""

    lines = ["🎛️  MIDI Ports Detected", "=" * 40]

    inputs = get_input_ports()
    if inputs:
        lines.append("\n🟢 INPUT PORTS:")
        for idx, name in enumerate(inputs, 1):
            lines.append(f"  {idx}. {name}")
    else:
        lines.append("\n🔴 No MIDI input ports detected.")

    outputs = get_output_ports()
    if outputs:
        lines.append("\n🔵 OUTPUT PORTS:")
        for idx, name in enumerate(outputs, 1):
            lines.append(f"  {idx}. {name}")
    else:
        lines.append("\n🔴 No MIDI output ports detected.")

    lines.append("\n" + "=" * 40)
    lines.append("Tip: Use these names with mido.open_input(<port>) / mido.open_output(<port>)")
    return "\n".join(lines)


__all__ = ["format_port_listing", "get_input_ports", "get_output_ports"]
