"""Command-line entry points for the drum project."""

from __future__ import annotations

import argparse
import time
from typing import Optional

from .gui import launch_gui
from .midi import USBMIDIReader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read MIDI events from a USB drum kit")
    parser.add_argument(
        "--port-keyword",
        default="USB",
        help="Substring used to pick the MIDI input port (defaults to 'USB').",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Log raw MIDI messages instead of launching the GUI.",
    )
    return parser


def run_gui(port_keyword: Optional[str]) -> None:
    launch_gui(port_keyword)


def run_headless(port_keyword: Optional[str]) -> None:
    reader = USBMIDIReader(port_keyword=port_keyword)
    try:
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        reader.stop()


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.headless:
        run_headless(args.port_keyword)
    else:
        run_gui(args.port_keyword)


__all__ = ["main", "run_gui", "run_headless", "build_parser"]
