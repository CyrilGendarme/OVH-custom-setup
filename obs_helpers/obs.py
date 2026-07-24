import json
from pathlib import Path

import obsws_python as obs

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def _load_config():
    for candidate in (BASE_DIR / "config.json", ROOT_DIR / "config.json"):
        if candidate.exists():
            with open(candidate, encoding="utf-8") as f:
                return json.load(f)
    return {}


CONFIG = _load_config()


class OBSController:

    def __init__(self):
        obs_config = CONFIG.get("obs", {})

        self.host = obs_config.get("host", "127.0.0.1")
        self.port = obs_config.get("port", 4455)
        self.password = obs_config.get("password", "")

        self.client = obs.ReqClient(
            host=self.host, port=self.port, password=self.password
        )

        self.radio_video_sources = [
            "vid 1",
            "vid 2",
            "vid 3",
        ]

        self.current_video_index = -1

    def get_scene_name(self):
        try:
            response = self.client.get_current_program_scene()
            return response.scene_name
        except Exception as exc:
            print(f"OBS get scene name failed: {exc}")
            return None

    def activate_macro(self, macro_name):

        # Name of hotkeys are to be found through helpers.py script

        try:
            if macro_name == "Typerwriter Radio":
                self.client.trigger_hot_key_by_name(
                    "macro_condition_hotkey_Macro trigger hotkey 2"
                )
            elif macro_name == "Typerwriter":
                self.client.trigger_hot_key_by_name(
                    "macro_condition_hotkey_Macro trigger hotkey 1"
                )

        except Exception as exc:
            print(f"OBS macro failed: {exc}")

    def set_source_visibility(self, source_name, visible):

        try:

            scene = self.get_scene_name()

            response = self.client.get_scene_item_list(scene)

            for item in response.scene_items:

                if item["sourceName"] == source_name:

                    self.client.set_scene_item_enabled(
                        scene_name=scene,
                        item_id=item["sceneItemId"],
                        enabled=visible,
                    )

                    return

        except Exception as exc:

            print(f"OBS visibility error {source_name}: {exc}")

    def switch_radio_background(self):

        self.current_video_index = (self.current_video_index + 1) % len(
            self.radio_video_sources
        )

        new_source = self.radio_video_sources[self.current_video_index]

        for source in self.radio_video_sources:

            self.set_source_visibility(source, source == new_source)

        print(f"Radio background switched to {new_source}")
