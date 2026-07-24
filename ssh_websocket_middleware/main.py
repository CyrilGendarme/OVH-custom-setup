import asyncio
import socket

from ssh_websocket_middleware.custom_queue import EventQueue
from ssh_websocket_middleware.websocket_server import TypewriterServer, TracklistServer
from obs_helpers.obs import OBSController
from queued_udp_receiver import QueuedUdpReceiver

port = 55555


    
async def main():
    queue = EventQueue()
    udp_receiver = QueuedUdpReceiver(queue, port=port)
    typewriter = TypewriterServer(queue)
    tracklist = TracklistServer(queue)
    await udp_receiver.start()
    await typewriter.start()
    await tracklist.start()

    obs = OBSController()

    print("Event system running")

    while True:
        event = await queue.get()
        # print("PLAYING:", event)

        if obs.get_scene_name() == "MAIN_DJ_SET":
            await typewriter.send(event)
            obs.activate_macro("Typerwriter")
            await asyncio.sleep(11)  # delay to ensure effect is fully achieved

        await tracklist.send(event)


asyncio.run(main())
