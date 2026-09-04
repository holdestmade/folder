"""Data update coordinator for the Folder integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import glob
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_FILTER,
    CONF_FOLDER_PATHS,
    DEFAULT_FILTER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class FolderData:
    """Contents of a monitored folder."""

    files: list[str]
    number_of_files: int
    size: int


def get_files_list(folder_path: str, filter_term: str) -> list[str]:
    """Return the list of files, applying filter."""
    query = os.path.join(folder_path, filter_term)
    return glob.glob(query)


def get_size(files_list: list[str]) -> int:
    """Return the sum of the size in bytes of files in the list."""
    size_list = [os.stat(f).st_size for f in files_list if os.path.isfile(f)]
    return sum(size_list)


class FolderCoordinator(DataUpdateCoordinator[FolderData]):
    """Poll a folder for its contents."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.path: str = entry.data[CONF_FOLDER_PATHS]
        self.filter_term: str = entry.options.get(
            CONF_FILTER, entry.data.get(CONF_FILTER, DEFAULT_FILTER)
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
            files = get_files_list(self.path, self.filter_term)
            size = get_size(files)
        except OSError as err:
            raise UpdateFailed(f"Error reading folder {self.path}: {err}") from err

        return FolderData(files=files, number_of_files=len(files), size=size)
