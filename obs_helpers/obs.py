import json
import re
import time
from datetime import datetime, timedelta
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
SCHEDULE_FILE = ROOT_DIR / "scripts" / "startingSoonSchedule.js"


def _extract_schedule_value(name, fallback=None):
    if not SCHEDULE_FILE.exists():
        return fallback

    content = SCHEDULE_FILE.read_text(encoding="utf-8")
    match = re.search(rf"export const {name} = ([^;]+);", content)
    if match is None:
        return fallback

    raw_value = match.group(1).strip()
    if raw_value == "null":
        return None

    try:
        return int(raw_value)
    except ValueError:
        return fallback


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
        self.starting_soon_radio_source = "vid 3"
        self.regular_radio_video_sources = [
            source
            for source in self.radio_video_sources
            if source != self.starting_soon_radio_source
        ]
        self.current_regular_video_index = -1

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
        time.sleep(0.1)
        self.set_source_visibility(source_name, True)
        print(f"Pulsed {source_name} in {current_scene}")
        return True

    def switch_radio_background(self):
        new_source = self.get_desired_radio_source(rotate_regular_source=True)
        if new_source is None:
            return

        self.set_radio_background_source(new_source)

    def _get_starting_soon_target(self):
        return (
            _extract_schedule_value("TARGET_HOUR"),
            _extract_schedule_value("TARGET_MINUTE"),
        )

    def _get_starting_soon_target_time(self, now=None):
        target_hour, target_minute = self._get_starting_soon_target()
        if target_hour is None or target_minute is None:
            return None

        now = now or datetime.now()
        target = now.replace(
            hour=target_hour,
            minute=target_minute,
            second=0,
            microsecond=0,
        )

        if target <= now:
            target += timedelta(days=1)

        return target

    def should_use_starting_soon_background(self, now=None):
        target = self._get_starting_soon_target_time(now=now)
        if target is None:
            return False

        now = now or datetime.now()
        remaining_seconds = int((target - now).total_seconds())

        return 0 < remaining_seconds <= 5 * 60

    def get_enabled_radio_source(self):
        try:
            scene = self.get_scene_name()
            if not scene:
                return None

            response = self.client.get_scene_item_list(scene)

            for item in response.scene_items:
                if (
                    item.get("sourceName") in self.radio_video_sources
                    and item.get("sceneItemEnabled")
                ):
                    return item["sourceName"]
        except Exception as exc:
            print(f"OBS enabled radio source error: {exc}")

        return None

    def get_desired_radio_source(self, rotate_regular_source=False):
        if self.should_use_starting_soon_background():
            return self.starting_soon_radio_source

        current_source = self.get_enabled_radio_source()
        if rotate_regular_source:
            self.current_regular_video_index = (
                self.current_regular_video_index + 1
            ) % len(self.regular_radio_video_sources)
            return self.regular_radio_video_sources[self.current_regular_video_index]

        if current_source in self.regular_radio_video_sources:
            self.current_regular_video_index = self.regular_radio_video_sources.index(
                current_source
            )
            return current_source

        if self.current_regular_video_index < 0:
            self.current_regular_video_index = 0

        return self.regular_radio_video_sources[self.current_regular_video_index]

    def set_radio_background_source(self, source_name):
        if source_name not in self.radio_video_sources:
            return

        for source in self.radio_video_sources:
            self.set_source_visibility(source, source == source_name)

        if source_name in self.regular_radio_video_sources:
            self.current_regular_video_index = self.regular_radio_video_sources.index(
                source_name
            )

        print(f"Radio background switched to {source_name}")

    def sync_radio_background(self):
        desired_source = self.get_desired_radio_source()
        if desired_source is None:
            return

        if self.get_enabled_radio_source() == desired_source:
            return

        self.set_radio_background_source(desired_source)
