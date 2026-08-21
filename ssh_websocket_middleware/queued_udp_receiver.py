import asyncio
import socket
import json

from ssh_websocket_middleware.custom_queue import EventQueue


class QueuedUdpReceiver:
    def __init__(self, queue: EventQueue, host, port, buffer_size=1024):
        self.queue = queue
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
        self.running = False

    def start_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.running = True

    async def start(self):
        """
        Start receiving UDP messages and pushing them into EventQueue.
        """
        self.start_socket()

        print(f"UDP receiver listening on {self.port}")

        while self.running:
            data, addr = await asyncio.to_thread(
                self.socket.recvfrom,
                self.buffer_size
            )

            try:
                message = data.decode("utf-8")

                # If your UDP sends JSON events
                event = json.loads(message)

            except Exception:
                # fallback for plain text messages
                event = {
                    "message": data.decode("utf-8", errors="replace")
                }

            print(f"Received UDP event from {addr}: {event}")

            await self.queue.put(event)

    def stop(self):
        self.running = False

        if self.socket:
            self.socket.close()