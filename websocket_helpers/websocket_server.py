from pathlib import Path
import websockets
import json

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def _load_config():
    for candidate in (BASE_DIR / "config.json", ROOT_DIR / "config.json"):
        if candidate.exists():
            with open(candidate, encoding="utf-8") as f:
                return json.load(f)
    return {}


config = _load_config()


class BroadcastServer:
    def __init__(self, queue, host, port, label="Overlay"):
        self.queue = queue
        self.clients = set()
        self.host = host
        self.port = port
        self.label = label

    async def handler(self, websocket, path=None):
        print(f"{self.label} connected")
        self.clients.add(websocket)

        try:
            async for msg in websocket:
                try:
                    event = json.loads(msg)
                except Exception:
                    event = {"message": str(msg)}

                if self.queue is not None:
                    await self.queue.put(event)
        finally:
            self.clients.discard(websocket)
            print(f"{self.label} disconnected")

    async def send(self, event):
        if not self.clients:
            return

        msg = json.dumps(event)
        disconnected = set()

        for client in list(self.clients):
            try:
                await client.send(msg)
            except Exception as exc:
                disconnected.add(client)
                print(f"Failed sending to a websocket client: {exc}")

        for client in disconnected:
            self.clients.discard(client)

        print(f"Sent event to {len(self.clients)} websocket(s): {event}")

    async def start(self):
        server = await websockets.serve(self.handler, self.host, self.port)
        print(f"{self.label} websocket listening on ws://{self.host}:{self.port}")
        return server


class TypewriterServer(BroadcastServer):
    def __init__(self, queue, config):
        section = config["overlay"]
        super().__init__(
            queue=queue,
            host=section["host"],
            port=section["port"],
            label="Typewriter",
        )


class TracklistServer(BroadcastServer):
    def __init__(self, queue, config):
        section = config["tracklist"]
        super().__init__(
            queue=queue,
            host=section["host"],
            port=section["port"],
            label="Tracklist",
        )
