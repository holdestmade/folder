"""Constants for the Folder integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "folder"

CONF_FOLDER_PATHS: Final = "folder"
CONF_FILTER: Final = "filter"

ATTR_PATH: Final = "path"
ATTR_FILTER: Final = "filter"
ATTR_NUMBER_OF_FILES: Final = "number_of_files"
ATTR_BYTES: Final = "bytes"
ATTR_FILE_LIST: Final = "file_list"

KEY_SIZE: Final = "size"
KEY_NUMBER_OF_FILES: Final = "number_of_files"

UNIT_FILES: Final = "files"

DEFAULT_FILTER: Final = "*"
DEFAULT_SCAN_INTERVAL: Final = 60

MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 86400
