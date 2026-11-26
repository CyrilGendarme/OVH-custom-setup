import asyncio
import socket
import json

from ssh_websocket_middleware.custom_queue import EventQueue

# Largest possible UDP payload. A smaller buffer silently truncates big
# datagrams on Linux and raises WinError 10040 on Windows.
MAX_UDP_SIZE = 65535

# Kernel receive buffer: absorbs bursts of messages (and fragment reassembly)
# while the event loop is busy, instead of dropping datagrams.
SOCKET_RCVBUF = 4 * 1024 * 1024


class QueuedUdpReceiver:
    def __init__(self, queue: EventQueue, host, port, buffer_size=MAX_UDP_SIZE):
        self.queue = queue
        self.host = host
        self.port = port
        self.buffer_size = max(buffer_size, MAX_UDP_SIZE)
        self.socket = None
        self.running = False

    def start_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow an immediate restart on the same port
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_RCVBUF)
        except OSError as e:
            print(f"Could not enlarge UDP receive buffer: {e}")
        self.socket.bind((self.host, self.port))
        # Wake the receive thread every second so stop() can end it cleanly
        self.socket.settimeout(1.0)
        self.running = True

    @staticmethod
    def parse(data: bytes):
        try:
            # If your UDP sends JSON events
            return json.loads(data.decode("utf-8"))
        except Exception:
            # fallback for plain text messages
            return {"message": data.decode("utf-8", errors="replace")}

    async def start(self):
        """
        Start receiving UDP messages and pushing them into EventQueue.
        """
        self.start_socket()

        rcvbuf = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        print(f"UDP receiver listening on {self.port} (kernel buffer {rcvbuf} bytes)")

        while self.running:
            try:
                data, addr = await asyncio.to_thread(
                    self.socket.recvfrom,
                    self.buffer_size
                )
            except socket.timeout:
                continue
            except OSError as e:
                if not self.running:
                    break  # socket closed by stop()
                # e.g. WinError 10054 (ICMP port unreachable) on Windows:
                # log and keep listening instead of killing the receiver
                print(f"UDP receive error (ignored): {e}")
                continue

            event = self.parse(data)
            preview = str(event)
            if len(preview) > 300:
                preview = preview[:300] + "..."
            print(f"Received UDP event from {addr} ({len(data)} bytes): {preview}")

            try:
                await self.queue.put(event)
            except Exception as e:
                print(f"Could not queue UDP event: {e}")

    def stop(self):
        self.running = False

        if self.socket:
            self.socket.close()
