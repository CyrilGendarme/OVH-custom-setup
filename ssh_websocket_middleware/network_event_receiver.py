"""Receive track events from rekordbox-databridge over the local network.

Counterpart of rekordbox-databridge/output/to_network.py. Zero configuration:

1. Listen for the sender's discovery beacon (UDP, default port 55557). It
   tells us the sender's current IP and its TCP port.
2. Connect over TCP and read newline-delimited JSON events into the queue.
   TCP retransmits lost packets, so events are not dropped by flaky Wi-Fi.
3. On disconnect, or when heartbeats stop, reconnect automatically.

The last sender address is cached on disk and retried directly, so
reconnecting does not depend on catching a beacon when the IP is unchanged.
"""

import asyncio
import json
import socket
import time
from pathlib import Path

from ssh_websocket_middleware.custom_queue import EventQueue

SERVICE_NAME = "rekordbox-databridge-events"
DEFAULT_BEACON_PORT = 55557
DEFAULT_TCP_PORT = 55556
HEARTBEAT_TIMEOUT_S = 15  # sender heartbeats every 5 s
RETRY_DELAY_S = 2
CACHE_FILE = Path.home() / ".cache" / "obs-middleware-last-sender.json"


class NetworkEventReceiver:
    def __init__(self, queue: EventQueue, beacon_port=DEFAULT_BEACON_PORT):
        self.queue = queue
        self.beacon_port = beacon_port
        self.sender = self._load_cached_sender()  # (ip, port) or None
        self.sender_seen_at = 0.0
        self._found = asyncio.Event()
        self._beacon_socket = None
        self._writer = None
        self._outage_reported = False  # one log line per outage
        self.running = False

    # ---- sender address cache -------------------------------------------

    @staticmethod
    def _load_cached_sender():
        try:
            data = json.loads(CACHE_FILE.read_text())
            return data["ip"], int(data["port"])
        except Exception:
            return None

    def _save_cached_sender(self):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            ip, port = self.sender
            CACHE_FILE.write_text(json.dumps({"ip": ip, "port": port}))
        except Exception:
            pass

    # ---- discovery ----------------------------------------------------------

    def _open_beacon_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        sock.bind(("", self.beacon_port))
        sock.settimeout(1.0)  # lets the receive thread notice stop()
        return sock

    def _on_beacon(self, data, addr):
        try:
            beacon = json.loads(data.decode())
            if beacon.get("service") != SERVICE_NAME:
                return
            sender = (addr[0], int(beacon.get("port", DEFAULT_TCP_PORT)))
        except Exception:
            return
        # A sender on this machine beacons via 127.0.0.1 and via the LAN;
        # keep the current address while it is alive to avoid flapping.
        if self.sender != sender and time.monotonic() - self.sender_seen_at > 5:
            print(f"Discovered event sender at {sender[0]}:{sender[1]}")
            self.sender = sender
            self._save_cached_sender()
        if self.sender == sender:
            self.sender_seen_at = time.monotonic()
        self._found.set()

    async def _listen_beacons(self):
        # Blocking recv in a thread: works on every Python 3 / Windows event loop
        while self.running:
            try:
                data, addr = await asyncio.to_thread(
                    self._beacon_socket.recvfrom, 1024
                )
            except socket.timeout:
                continue
            except OSError:
                if not self.running:
                    return
                await asyncio.sleep(1)
                continue
            self._on_beacon(data, addr)

    # ---- event stream -------------------------------------------------------

    async def _stream_events(self, ip, port):
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=5
        )
        self._writer = writer
        sock = writer.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        print(f"Connected to event sender {ip}:{port}")
        self._outage_reported = False
        try:
            while self.running:
                line = await asyncio.wait_for(
                    reader.readline(), timeout=HEARTBEAT_TIMEOUT_S
                )
                if not line:
                    raise ConnectionError("sender closed the connection")
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    print(f"Ignoring malformed event line: {line[:200]!r}")
                    continue
                if not isinstance(event, dict) or event.get("type") == "heartbeat":
                    continue
                preview = str(event)
                if len(preview) > 300:
                    preview = preview[:300] + "..."
                print(f"Received event: {preview}")
                await self.queue.put(event)
        finally:
            self._writer = None
            writer.close()

    async def _connection_loop(self):
        while self.running:
            if self.sender is None:
                print(f"Waiting for event sender beacon on UDP {self.beacon_port}...")
                await self._found.wait()
            self._found.clear()
            ip, port = self.sender
            try:
                await self._stream_events(ip, port)
            except asyncio.TimeoutError:
                if not self._outage_reported:
                    print(f"Event sender {ip}:{port} silent or unreachable, "
                          "reconnecting automatically")
                self._outage_reported = True
            except (OSError, ConnectionError) as e:
                if not self._outage_reported:
                    print(f"Event sender {ip}:{port} unavailable ({e}), "
                          "reconnecting automatically")
                self._outage_reported = True
            if not self.running:
                return
            # Retry the known address, or switch as soon as a beacon says it moved
            try:
                await asyncio.wait_for(self._found.wait(), timeout=RETRY_DELAY_S)
            except asyncio.TimeoutError:
                pass

    # ---- lifecycle ----------------------------------------------------------

    async def start(self):
        self.running = True
        self._beacon_socket = self._open_beacon_socket()
        print(f"Event receiver: discovery on UDP {self.beacon_port}"
              + (f", last sender {self.sender[0]}:{self.sender[1]}" if self.sender else ""))
        await asyncio.gather(self._listen_beacons(), self._connection_loop())

    def stop(self):
        self.running = False
        self._found.set()
        if self._writer:
            self._writer.close()
        if self._beacon_socket:
            self._beacon_socket.close()
