import logging
import time
from pathlib import Path

import obsws_python as obs

from config import CONFIG, ROOT_DIR

# obsws_python logs a full traceback before re-raising; failures are reported below instead.
logging.getLogger("obsws_python").setLevel(logging.CRITICAL)


class OBSController:

    def __init__(self):
        obs_config = CONFIG.get("obs", {})

        self.host = obs_config["host"]
        self.port = obs_config["port"]
        self.password = obs_config.get("password", "")

        self._client = None
        self._connect()

    def _connect(self):
        try:
            self._client = obs.ReqClient(
                host=self.host, port=self.port, password=self.password
            )
        except Exception as exc:
            self._client = None
            print(f"OBS connection to {self.host}:{self.port} failed: {exc}")
        return self._client

    @property
    def client(self):
        # Reconnect lazily so OBS can be started (or restarted) after this process.
        if self._client is None and self._connect() is None:
            raise ConnectionError("OBS websocket not connected")
        return self._client

    def get_scene_name(self):
        try:
            response = self.client.get_current_program_scene()
            return response.scene_name
        except Exception as exc:
            print(f"OBS get scene name failed: {exc}")
            self._client = None
            return None

    def activate_macro(self, macro_name):

        # Name of hotkeys are to be found through helpers.py script

        try:
            if macro_name == "Typerwriter Radio":
                self.client.trigger_hot_key_by_name(self._macro_hotkey(2))
            elif macro_name == "Typerwriter":
                self.client.trigger_hot_key_by_name(self._macro_hotkey(1))

        except Exception as exc:
            print(f"OBS macro failed: {exc}")

    def _macro_hotkey(self, number):
        # Advanced Scene Switcher localizes hotkey names with OBS's UI language
        # (e.g. "Macro trigger hotkey 1" / "Raccourci clavier de déclenchement de macro 1"),
        # so match on the prefix and trailing number only.
        for name in self.client.get_hot_key_list().hotkeys:
            if name.startswith("macro_condition_hotkey_") and name.endswith(f" {number}"):
                return name
        raise LookupError(f"No Advanced Scene Switcher macro hotkey #{number} in OBS")

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
