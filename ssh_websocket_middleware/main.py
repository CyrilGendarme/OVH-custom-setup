import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ssh_websocket_middleware.custom_queue import EventQueue
from ssh_websocket_middleware.websocket_server import (
    TypewriterServer,
    LastTracksServer,
    config as websocket_config,
)
from obs_helpers.obs import OBSController
from queued_udp_receiver import QueuedUdpReceiver

port = 55555


    
async def main():
    queue = EventQueue()
    udp_receiver = QueuedUdpReceiver(queue, port=port)
    typewriter = TypewriterServer(queue, websocket_config)
    tracklist = LastTracksServer(queue, websocket_config)
    udp_task = asyncio.create_task(udp_receiver.start())

    # Keep references so websocket servers stay alive for the process lifetime.
    _typewriter_server = await typewriter.start()
    _tracklist_server = await tracklist.start()

    obs = OBSController()

    try:
        while True:
            event = await queue.get()
            if obs.get_scene_name() == "MAIN_DJ_SET":
                await typewriter.send(event)
                # obs.activate_macro("Typerwriter")
                obs.activate_macro("Typerwriter")
                await asyncio.sleep(11)  # delay to ensure effect is fully achieved

            await tracklist.send(event)
    finally:
        udp_receiver.stop()
        udp_task.cancel()


asyncio.run(main())
