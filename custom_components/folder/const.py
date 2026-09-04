"""Constants for the Folder integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "folder"

CONF_FOLDER_PATHS: Final = "folder"
CONF_FILTER: Final = "filter"

DEFAULT_FILTER: Final = "*"
DEFAULT_SCAN_INTERVAL: Final = 60

MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 86400
