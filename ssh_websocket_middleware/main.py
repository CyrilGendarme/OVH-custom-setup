import asyncio
import json
from pathlib import Path


from custom_queue import EventQueue
from websocket_server import TypewriterServer, TracklistServer
from ssh_receiver import SSHReceiver
from obs import OBSController

BASE_DIR = Path(__file__).resolve().parent


with open(BASE_DIR / "config.json", encoding="utf-8") as f:
    config = json.load(f)


async def main():
    queue = EventQueue()
    typewriter = TypewriterServer(queue, config)
    tracklist = TracklistServer(queue, config)
    await typewriter.start()
    await tracklist.start()

    ssh = SSHReceiver(queue, config)
    await ssh.start()

    obs = OBSController(config)

    print("Event system running")

    while True:
        event = await queue.get()
        # print("PLAYING:", event)

        if obs.get_scene_name() == "MAIN_DJ_SET":
            await typewriter.send(event)
            if obs is not None:
                obs.activate_macro("Typerwriter")
            await asyncio.sleep(11)  # delay to ensure effect is fully achieved

        await tracklist.send(event)


asyncio.run(main())
