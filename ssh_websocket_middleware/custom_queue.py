import asyncio
from itertools import count


class EventQueue:
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self._sequence = count()

    async def put(self, event):
        priority = event.get("priority", 5)
        await self.queue.put((-priority, next(self._sequence), event))

    async def get(self):
        priority, sequence, event = await self.queue.get()
        return event

    def empty(self):
        return self.queue.empty()
