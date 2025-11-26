"""Basic tests for the MIDI helper utilities."""

from __future__ import annotations

from unittest import mock

from drum_app import midi


def test_wait_for_midi_input_returns_matching_name() -> None:
    with mock.patch("drum_app.midi.mido.get_input_names", return_value=["USB Drum", "Other"]):
        assert midi.wait_for_midi_input("usb") == "USB Drum"


def test_wait_for_midi_input_falls_back_to_first_port_when_no_keyword() -> None:
    with mock.patch("drum_app.midi.mido.get_input_names", return_value=["Primary", "Secondary"]):
        assert midi.wait_for_midi_input(keyword=None) == "Primary"


def test_usb_midi_reader_opens_port_and_stops_cleanly() -> None:
    dummy_port = mock.Mock()
    dummy_port.iter_pending.return_value = []

    with mock.patch("drum_app.midi.wait_for_midi_input", return_value="Dummy"), mock.patch(
        "drum_app.midi.mido.open_input", return_value=dummy_port
    ):
        reader = midi.USBMIDIReader()
        assert reader.port is dummy_port
        reader.stop()
        dummy_port.close.assert_called_once()
