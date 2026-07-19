import asyncio

from websocket_helpers.custom_queue import EventQueue
from websocket_helpers.websocket_server import TypewriterServer, TracklistServer
from ssh_receiver import SSHReceiver
from obs_helpers.obs import OBSController

async def main():
    queue = EventQueue()
    typewriter = TypewriterServer(queue)
    tracklist = TracklistServer(queue)
    await typewriter.start()
    await tracklist.start()

    ssh = SSHReceiver(queue)
    await ssh.start()

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
