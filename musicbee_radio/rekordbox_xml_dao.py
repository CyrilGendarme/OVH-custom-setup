from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any

from config import CONFIG, resolve_path


REKORDBOX_COLLECTION_TRACKS_XML_FILE_PATH = resolve_path(
    CONFIG["paths"]["rekordbox_xml"]
)


class RekordboxDAO:
    """Simple XML DAO to retrieve Rekordbox track data by title and artist."""

    def __init__(self, xml_path: str | Path | None = None) -> None:
        self.xml_path = Path(xml_path or REKORDBOX_COLLECTION_TRACKS_XML_FILE_PATH)
        self._tree: ET.ElementTree | None = None
        self._tracks_by_key: dict[tuple[str, str], ET.Element] = {}
        self._load_xml()

    def _load_xml(self) -> None:
        if not self.xml_path.exists():
            raise FileNotFoundError(f"Rekordbox XML not found: {self.xml_path}")

        self._tree = ET.parse(self.xml_path)
        self._tracks_by_key.clear()

        root = self._tree.getroot()
        collection = root.find("COLLECTION")
        if collection is None:
            return

        for track in collection.findall("TRACK"):
            title = self._normalize(track.attrib.get("Name", ""))
            artist = self._normalize(track.attrib.get("Artist", ""))
            if title and artist:
                self._tracks_by_key[(artist, title)] = track

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.strip().casefold().split())



    def get_track_data(self, title: str, artist: str) -> dict[str, Any] | None:
        """Return all available XML data for a track matched by artist + title."""
        key = (self._normalize(artist), self._normalize(title))
        track = self._tracks_by_key.get(key)
        
        if track is None:
            return None

        return dict(track.attrib)
        
