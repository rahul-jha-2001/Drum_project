"""CLI helper that prints detected MIDI input/output ports."""

from drum_app.ports import format_port_listing


def list_midi_ports() -> None:
    print(format_port_listing())


if __name__ == "__main__":
    list_midi_ports()
