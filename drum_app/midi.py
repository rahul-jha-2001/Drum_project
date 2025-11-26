import time
import threading
from typing import Optional, Callable, List
import mido


class USBMIDIReader:
    """
    Unified MIDI reader object.
    - Lists all input ports
    - Auto-detects (keyword match)
    - Allows manual port selection
    - Reads MIDI messages on a background thread
    """

    def __init__(
        self,
        port_keyword: Optional[str] = "USB",
        poll_interval: float = 0.01,
        message_handler: Optional[Callable[[mido.Message], None]] = None,
        auto_start: bool = True,
        timeout: float = 15.0,
    ) -> None:

        self.port_keyword = port_keyword
        self.poll_interval = poll_interval
        self.message_handler = message_handler or self._default_handler
        self.timeout = timeout

        self.port_name: Optional[str] = None
        self.port: Optional[mido.ports.BaseInput] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

        if auto_start:
            self.start()

    # -----------------------------
    # 🔍 PORT DISCOVERY
    # -----------------------------

    @staticmethod
    def list_ports() -> List[str]:
        """Return all available MIDI input port names."""
        ports = mido.get_input_names()
        print("\n🎹 Available MIDI Input Ports:")
        for i, p in enumerate(ports):
            print(f"  {i}: {p}")
        print()
        return ports

    def _auto_detect_port(self) -> str:
        """Detect port based on keyword."""

        deadline = time.time() + self.timeout

        while time.time() < deadline:
            for p in mido.get_input_names():
                if self.port_keyword and self.port_keyword.lower() in p.lower():
                    return p
            time.sleep(0.2)

        raise TimeoutError(
            f"❌ Could not find MIDI port containing keyword '{self.port_keyword}'."
        )

    # -----------------------------
    # 🎛 START / STOP
    # -----------------------------

    def start(self, port_name: Optional[str] = None) -> None:
        """Start reading from a specific port or auto-detect one."""

        if self.running:
            return

        # manual override
        if port_name is not None:
            self.port_name = port_name
        else:
            self.port_name = self._auto_detect_port()

        print(f"[✅] Connected to MIDI input: {self.port_name}")

        # open the port
        self.port = mido.open_input(self.port_name)

        # start background thread
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Stop the MIDI reader."""
        if not self.running:
            return

        self.running = False

        if self.thread:
            self.thread.join()

        if self.port:
            self.port.close()

        print("[🛑] MIDI reader stopped.")

    # -----------------------------
    # 🎧 BACKGROUND READING
    # -----------------------------

    def _read_loop(self) -> None:
        while self.running and self.port:
            for msg in self.port.iter_pending():
                self.message_handler(msg)
            time.sleep(self.poll_interval)

    @staticmethod
    def _default_handler(msg) -> None:
        print("[MIDI]", msg)

    # -----------------------------
    # 🧹 CONTEXT MANAGER
    # -----------------------------

    def __enter__(self) -> "USBMIDIReader":
        if not self.running:
            self.start()
        return this

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()
