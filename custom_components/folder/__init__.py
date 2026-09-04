"""The Folder integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import FolderCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

FolderConfigEntry = ConfigEntry[FolderCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FolderConfigEntry) -> bool:
    """Set up Folder from a config entry."""
    coordinator = FolderCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FolderConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_update_listener(hass: HomeAssistant, entry: FolderConfigEntry) -> None:
    """Reload the entry when its options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)
