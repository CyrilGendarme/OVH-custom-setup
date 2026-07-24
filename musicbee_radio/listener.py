import asyncio
from pathlib import Path
import sys

from rekordbox_xml_dao import RekordboxDAO

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from obs_helpers.obs import OBSController
from ssh_websocket_middleware.websocket_server import BroadcastServer

MUSICBEE_TAGS = Path(__file__).resolve().parent / "now_played_track_info" / "Tags.txt"

WS_HOST = "127.0.0.1"
TYPEWRITER_PORT = 8765
NOW_PLAYING_PORT = 8766


def _safe_get(items, index):
    if index < len(items):
        return items[index].strip()
    return ""


def parse_track_text(track):
    items = [line.strip() for line in track.replace("\\n", "\n").split("\n")]
    artist = _safe_get(items, 0)
    album = _safe_get(items, 1)
    title = _safe_get(items, 2)
    year = _safe_get(items, 3)
    return artist, album, title, year


async def main():
    dao = RekordboxDAO()
    last_track = None
    obs = None

    try:
        obs = OBSController()
    except Exception as exc:
        print(f"OBS unavailable, macro trigger disabled: {exc}")

    typewriter_ws = BroadcastServer(None, WS_HOST, TYPEWRITER_PORT, "Typewriter")
    now_playing_ws = BroadcastServer(None, WS_HOST, NOW_PLAYING_PORT, "NowPlaying")

    await typewriter_ws.start()
    await now_playing_ws.start()

    while True:
        try:
            if MUSICBEE_TAGS.exists():
                track = MUSICBEE_TAGS.read_text(encoding="utf-8-sig").strip()

                if track and track != last_track:
                    print("\nNEW TRACK")
                    print(track)
                    last_track = track

                    artist_name, album_name, track_name, year = parse_track_text(track)

                    event = {
                        "artist": artist_name,
                        "title": track_name,
                        "track": track_name,
                        "album": album_name,
                        "year": year,
                    }

                    data = dao.get_track_data(title=track_name, artist=artist_name)
                    if data is not None:
                        event["label"] = data.get("Label") or ""
                        event["bpm"] = str(data.get("AverageBpm") or "")
                        event["tonality"] = data.get("Tonality") or ""
                        event["genre"] = data.get("Genre") or ""

                        if not event["album"]:
                            event["album"] = str(data.get("Album") or "")

                        if not event["year"]:
                            event["year"] = str(data.get("Year") or "")
                    else:
                        event["label"] = ""
                        event["bpm"] = ""
                        event["tonality"] = ""
                        event["genre"] = ""

                    event["message"] = (
                        f"{event['artist']} - {event['title']}"
                        if event["artist"] and event["title"]
                        else event["title"] or event["artist"]
                    )
                            
                    print(f"obs.get_scene_name() = {obs.get_scene_name() if obs is not None else 'None'}")

                    if obs is not None and obs.get_scene_name() == "MAIN_RADIO":
                        await typewriter_ws.send(event)
                        obs.switch_radio_background()
                        obs.activate_macro("Typerwriter Radio")
                        await asyncio.sleep(
                            11
                        )  # delay to ensure effect is fully achieved

                    await now_playing_ws.send(event)

        except Exception as exc:
            print(exc)

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
