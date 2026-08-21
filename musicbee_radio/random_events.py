import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from config import CONFIG, resolve_path
from obs_helpers.obs import OBSController

TRACK_DURATION_DATA = resolve_path(CONFIG["paths"]["track_duration_data"])
RANDOM_EVENT_CONFIG = CONFIG["random_events"]
MINIMUM_ELAPSED_TRACK_SECONDS = RANDOM_EVENT_CONFIG["minimum_elapsed_track_seconds"]
MINIMUM_REMAINING_TRACK_SECONDS = RANDOM_EVENT_CONFIG["minimum_remaining_track_seconds"]


def load_random_event_settings():
	settings = CONFIG.get("random_events", {})
	item_name = settings.get("item_name")
	time_1 = settings.get("time_1")
	time_2 = settings.get("time_2")

	if not item_name:
		raise ValueError("config.random_events.item_name must be configured")

	if not isinstance(time_1, (int, float)) or not isinstance(
		time_2, (int, float)
	):
		raise ValueError("config.random_events.time_1 and time_2 must be numbers")

	if time_1 <= 0 or time_2 <= 0:
		raise ValueError("config.random_events.time_1 and time_2 must be > 0")

	if time_1 > time_2:
		raise ValueError(
			"config.random_events.time_1 must be <= config.random_events.time_2"
		)

	return item_name, float(time_1), float(time_2)


def parse_duration_to_seconds(raw_duration):
	raw_duration = raw_duration.strip()
	if not raw_duration:
		return None

	if raw_duration.isdigit():
		return int(raw_duration)

	parts = raw_duration.split(":")
	if not all(part.isdigit() for part in parts):
		return None

	if len(parts) == 2:
		minutes, seconds = (int(part) for part in parts)
		return minutes * 60 + seconds

	if len(parts) == 3:
		hours, minutes, seconds = (int(part) for part in parts)
		return hours * 3600 + minutes * 60 + seconds

	return None


def get_track_timing(now=None):
	if not TRACK_DURATION_DATA.exists():
		return None, None

	lines = [
		line.strip()
		for line in TRACK_DURATION_DATA.read_text(encoding="utf-8").splitlines()
		if line.strip()
	]
	if len(lines) < 2:
		return None, None

	try:
		started_at_time = datetime.strptime(lines[0], "%H:%M:%S").time()
	except ValueError:
		return None, None

	duration_seconds = parse_duration_to_seconds(lines[1])
	if duration_seconds is None:
		return None, None

	now = now or datetime.now()
	started_at = datetime.combine(now.date(), started_at_time)
	if started_at > now:
		started_at -= timedelta(days=1)

	elapsed_seconds = int((now - started_at).total_seconds())
	remaining_seconds = duration_seconds - elapsed_seconds
	return elapsed_seconds, remaining_seconds


def get_remaining_track_seconds(now=None):
	_, remaining_seconds = get_track_timing(now=now)
	return remaining_seconds


async def main():
	item_name, time_1, time_2 = load_random_event_settings()
	obs = OBSController()

	print(
		"Random radio events active for "
		f"{item_name} with delay range {time_1:.0f}s to {time_2:.0f}s"
	)

	while True:
		wait_seconds = random.uniform(time_1, time_2)
		print(f"Next random event in {wait_seconds:.2f}s")
		await asyncio.sleep(wait_seconds)

		try:
			elapsed_seconds, remaining_seconds = get_track_timing()
			if (
				elapsed_seconds is not None
				and elapsed_seconds < MINIMUM_ELAPSED_TRACK_SECONDS
			):
				print(
					"Random event delayed because track has only been playing for "
					f"{elapsed_seconds}s"
				)
				continue

			if (
				remaining_seconds is not None
				and remaining_seconds < MINIMUM_REMAINING_TRACK_SECONDS
			):
				print(
					"Random event delayed because remaining track time is "
					f"{remaining_seconds}s"
				)
				continue

			triggered = obs.pulse_current_scene_item(item_name)
			if not triggered:
				print("Random event skipped because current scene is not MAIN_RADIO")
		except Exception as exc:
			print(f"Random event failed: {exc}")


if __name__ == "__main__":
	asyncio.run(main())
