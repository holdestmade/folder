"""Data update coordinator for the Folder integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import fnmatch
import glob
import logging
import os
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_FILTER,
    CONF_FOLDER_PATHS,
    CONF_RECURSIVE,
    DEFAULT_FILTER,
    DEFAULT_RECURSIVE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FILTER_SEPARATOR,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class FolderData:
    """Contents of a monitored folder."""

    files: list[str]
    number_of_files: int
    size: int


def parse_filter(filter_term: str) -> list[str]:
    """Split a filter into its patterns.

    The filter is a comma separated list, so "*.mkv, *.mp4" selects both
    extensions. A filter with no comma is a single pattern and behaves exactly
    as it always has.
    """
    patterns = [pattern.strip() for pattern in filter_term.split(FILTER_SEPARATOR)]
    return [pattern for pattern in patterns if pattern] or [DEFAULT_FILTER]


def any_case(pattern: str) -> str:
    """Expand the letters in a glob pattern so it matches either case.

    glob() has no case insensitive mode, so "*.mkv" becomes "*.[mM][kK][vV]".
    Characters inside a [...] class are left alone rather than risk corrupting
    the class.
    """
    expanded: list[str] = []
    in_class = False
    for char in pattern:
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif not in_class and char.isalpha():
            lower, upper = char.lower(), char.upper()
            if lower != upper and len(lower) == len(upper) == 1:
                expanded.append(f"[{lower}{upper}]")
                continue
        expanded.append(char)
    return "".join(expanded)


def compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    """Compile filter patterns into case insensitive matchers for file names."""
    return [re.compile(fnmatch.translate(pattern), re.IGNORECASE) for pattern in patterns]


def walk_files(folder_path: str, patterns: list[str]) -> list[str]:
    """Return names matching any pattern in folder_path and its subfolders.

    Symlinked directories are deliberately not followed. glob()'s "**" does
    follow them, which walks a symlink cycle until the path length limit stops
    it and reports files outside the configured folder.
    """
    matchers = compile_patterns(patterns)
    files_list: list[str] = []
    for root, dirs, files in os.walk(folder_path):
        # glob() never matches a leading dot, so skip hidden files and do not
        # descend into hidden directories, keeping both modes consistent.
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        files_list.extend(
            os.path.join(root, name)
            for name in files
            if not name.startswith(".")
            and any(matcher.match(name) for matcher in matchers)
        )
    return files_list


def get_files_list(
    folder_path: str, filter_term: str, recursive: bool = False
) -> list[str]:
    """Return the list of files, applying filter."""
    patterns = parse_filter(filter_term)
    if recursive:
        matches = walk_files(folder_path, patterns)
    else:
        # glob.escape keeps brackets in the folder name, as in "TV [4K]", from
        # being read as part of the pattern.
        root = glob.escape(folder_path)
        matches = [
            path
            for pattern in patterns
            for path in glob.glob(os.path.join(root, any_case(pattern)))
        ]
    # Overlapping patterns can match the same file twice, so keep the first
    # occurrence of each. A bare "*" filter also matches subdirectories; count
    # only real files, so number_of_files agrees with the bytes attribute about
    # what a file is.
    return [path for path in dict.fromkeys(matches) if os.path.isfile(path)]


def get_size(files_list: list[str]) -> int:
    """Return the sum of the size in bytes of files in the list."""
    size = 0
    for path in files_list:
        try:
            size += os.stat(path).st_size
        except OSError:
            # The file went away between listing and stat-ing it.
            continue
    return size


class FolderCoordinator(DataUpdateCoordinator[FolderData]):
    """Poll a folder for its contents."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.path: str = entry.data[CONF_FOLDER_PATHS]
        self.filter_term: str = entry.options.get(
            CONF_FILTER, entry.data.get(CONF_FILTER, DEFAULT_FILTER)
        )
        self.recursive: bool = bool(
            entry.options.get(
                CONF_RECURSIVE, entry.data.get(CONF_RECURSIVE, DEFAULT_RECURSIVE)
            )
        )
        scan_interval: int = int(
            entry.options.get(
                CONF_SCAN_INTERVAL,
                entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {self.path}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> FolderData:
        """Fetch the folder contents."""
        if not self.hass.config.is_allowed_path(self.path):
            raise ConfigEntryError(
                f"Folder {self.path} is not allowed, please add it to "
                "allowlist_external_dirs in configuration.yaml"
            )

        return await self.hass.async_add_executor_job(self._scan)

    def _scan(self) -> FolderData:
        """Scan the folder. Runs in the executor."""
        if not os.path.isdir(self.path):
            raise UpdateFailed(f"Folder {self.path} is not a directory")

        try:
            files = get_files_list(self.path, self.filter_term, self.recursive)
            size = get_size(files)
        except OSError as err:
            raise UpdateFailed(f"Error reading folder {self.path}: {err}") from err

        return FolderData(files=files, number_of_files=len(files), size=size)
