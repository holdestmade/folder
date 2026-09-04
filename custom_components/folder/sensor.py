"""Sensor for monitoring the contents of a folder."""

from __future__ import annotations

import os

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FolderConfigEntry
from .const import CONF_FILTER, CONF_FOLDER_PATHS, DEFAULT_FILTER, DOMAIN
from .coordinator import FolderCoordinator

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FOLDER_PATHS): cv.isdir,
        vol.Optional(CONF_FILTER, default=DEFAULT_FILTER): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import a YAML configured folder sensor into a config entry."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        breaks_in_ha_version=None,
        is_fixable=False,
        issue_domain=DOMAIN,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={"path": config[CONF_FOLDER_PATHS]},
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=dict(config),
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FolderConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the folder sensor from a config entry."""
    async_add_entities([FolderSensor(entry.runtime_data, entry)])


class FolderSensor(CoordinatorEntity[FolderCoordinator], SensorEntity):
    """Representation of a folder."""

    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:folder"
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: FolderCoordinator, entry: FolderConfigEntry
    ) -> None:
        """Initialize the data object."""
        super().__init__(coordinator)
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title or os.path.basename(coordinator.path),
        )

    @property
    def native_value(self) -> float:
        """Return the total size of the matched files in megabytes."""
        return round(self.coordinator.data.size / 1e6, 2)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Return the state attributes."""
        data = self.coordinator.data
        return {
            "path": os.path.join(self.coordinator.path, ""),
            "filter": self.coordinator.filter_term,
            "number_of_files": data.number_of_files,
            "bytes": data.size,
            "file_list": data.files,
        }
