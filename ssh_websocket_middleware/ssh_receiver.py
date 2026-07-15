import asyncio
import json
import threading


class SSHReceiver:
    def __init__(self, queue, config=None):
        self.queue = queue
        config = config or {}
        self.prompt =  "TEST> "
        self._task = None
        self._running = False
        self._loop = None
        self._thread = None

    def _build_event(self, raw_message):
        try:
            event = json.loads(raw_message)
            if not isinstance(event, dict):
                raise ValueError("Mock input must be a JSON object or plain text")

        except Exception:
            event = {
                "message": raw_message,
            }

        event.setdefault("source", "mock")
        return event

    def _build_default_event(self):
        return {
            "source": "mock",
            "type": "track_played",
            "title": "what a title for a song",
            "artist": "super good artist or somethin"
        }

    def _enqueue_event(self, event):
        if self._loop is None:
            return

        future = asyncio.run_coroutine_threadsafe(self.queue.put(event), self._loop)
        future.result()

    def _listen_console(self):
        while self._running:
            try:
                raw_message = input(self.prompt)

            except EOFError:
                return

            raw_message = raw_message.strip()

            if not raw_message:
                event = self._build_default_event()
                print("Mock Enter pressed:", event)
                self._enqueue_event(event)
                print("Mock event queued")
                continue

            if raw_message.lower() in {"exit", "quit"}:
                self._running = False
                return

            event = self._build_event(raw_message)
            print("Mock input received:", event)

            self._enqueue_event(event)
            print("Mock event queued")

    async def start(self):
        if self._task is not None:
            return

        self._running = True
        self._loop = asyncio.get_running_loop()
        self._thread = threading.Thread(target=self._listen_console, daemon=True)
        self._thread.start()
        print("Mock event input enabled. Press Enter to send a generic JSON event.")
