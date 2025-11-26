# Drum Project

``app.py`` (or ``python -m drum_app.cli``) launches the application. By default
it opens the Tkinter GUI that lights up when pads are struck on the connected
Alesis kit. Pass ``--headless`` to dump raw MIDI messages to the terminal.

## Repository Layout

- ``drum_app/`` – Python package that contains the reusable building blocks.
  - ``midi.py`` wires up the ``USBMIDIReader`` helper and the
    ``wait_for_midi_input`` discovery function.
  - ``gui.py`` houses the Tkinter UI widgets and the drum hit display logic.
  - ``ports.py`` centralises MIDI port listing helpers.
  - ``assets/`` keeps images, icons, and future UI resources in one place.
- ``scripts/`` – small helper CLIs. ``list_midi_ports.py`` mirrors
  ``drum_app.ports`` to make debugging connections easy.
- ``midi_port.py`` – quick wrapper that prints the first port containing a
  keyword (defaults to ``USB``).
- ``tests/`` – lightweight tests that exercise the MIDI utilities without
  needing actual hardware.
- ``requirements.txt`` – runtime dependencies (``mido`` + ``python-rtmidi``).

## Usage

```bash
python app.py                # launch GUI
python app.py --headless     # log raw MIDI events
python scripts/list_midi_ports.py
python midi_port.py Ride     # find first port with "Ride" in its name
```
