import time
from pathlib import Path

import obsws_python as obs

from config import CONFIG, ROOT_DIR


class OBSController:

    def __init__(self):
        obs_config = CONFIG.get("obs", {})

        self.host = obs_config["host"]
        self.port = obs_config["port"]
        self.password = obs_config.get("password", "")

        self.client = obs.ReqClient(
            host=self.host, port=self.port, password=self.password
        )

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

    def pulse_current_scene_item(self, source_name, scene_name="MAIN_RADIO"):
        current_scene = self.get_scene_name()
        if current_scene != scene_name:
            return False

        self.set_source_visibility(source_name, False)
        time.sleep(1)
        self.set_source_visibility(source_name, True)
        print(f"Pulsed {source_name} in {current_scene}")
        return True
