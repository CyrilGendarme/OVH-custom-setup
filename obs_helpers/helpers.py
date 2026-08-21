import sys
from pathlib import Path

import obsws_python as obs

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import CONFIG

obs_config = CONFIG["obs"]
client = obs.ReqClient(
    host=obs_config["host"],
    port=obs_config["port"],
    password=obs_config.get("password", ""),
)


scene_names = [
    "MAIN_DJ_SET",
    "SOCIAL_MEDIA_BOTTOM_LEFT",
    "TYPEWRITER",
    "LAST_TRACKS_BOTTOM_LEFT"
]

for scene_name in scene_names:
    resp = client.get_scene_item_list(name=scene_name)
    print(f"---\nScene: {scene_name}")
    for item in resp.scene_items:
        print(item["sourceName"], item["sceneItemId"])
        
        
print("\n\nHotkeys:")

hotkey_response = client.get_hot_key_list()
hotkeys = getattr(hotkey_response, "hotkeys", None)

if hotkeys is None:
    hotkeys = getattr(hotkey_response, "hot_keys", None)

if isinstance(hotkeys, dict):
    for hotkey_name in hotkeys.keys():
        print(hotkey_name)
elif isinstance(hotkeys, (list, tuple, set)):
    for hotkey in hotkeys:
        print(hotkey)
else:
    print("Unexpected hotkey response shape:", type(hotkey_response).__name__)
    print(hotkey_response)