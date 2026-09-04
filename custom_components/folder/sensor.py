"""Sensors for monitoring the contents of a folder."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import os

import voluptuous as vol

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
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
from .const import (
    ATTR_BYTES,
    ATTR_FILE_LIST,
    ATTR_FILTER,
    ATTR_NUMBER_OF_FILES,
    ATTR_PATH,
    CONF_FILTER,
    CONF_FOLDER_PATHS,
    DEFAULT_FILTER,
    DOMAIN,
    KEY_NUMBER_OF_FILES,
    KEY_SIZE,
    UNIT_FILES,
)
from .coordinator import FolderCoordinator, FolderData

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_FOLDER_PATHS): cv.isdir,
        vol.Optional(CONF_FILTER, default=DEFAULT_FILTER): cv.string,
    }
)


@dataclass(frozen=True, kw_only=True)
class FolderSensorEntityDescription(SensorEntityDescription):
    """Describes a folder sensor."""

    value_fn: Callable[[FolderData], float | int]


SENSOR_TYPES: tuple[FolderSensorEntityDescription, ...] = (
    FolderSensorEntityDescription(
        key=KEY_SIZE,
        # Unnamed, so it inherits the device (folder) name and keeps the
        # entity_id the YAML platform used.
        name=None,
        icon="mdi:folder",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        suggested_display_precision=2,
        value_fn=lambda data: round(data.size / 1e6, 2),
    ),
    FolderSensorEntityDescription(
        key=KEY_NUMBER_OF_FILES,
        translation_key=KEY_NUMBER_OF_FILES,
        icon="mdi:file-multiple",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_FILES,
        value_fn=lambda data: data.number_of_files,
    ),
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
    """Set up the folder sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        FolderSensor(coordinator, entry, description) for description in SENSOR_TYPES
    )


class FolderSensor(CoordinatorEntity[FolderCoordinator], SensorEntity):
    """Representation of a folder."""

    # The file list can grow past the recorder's 16 KiB attribute limit, which
    # makes it drop the whole attribute set for this entity. Keep it in the
    # state machine but out of the database.
    _unrecorded_attributes = frozenset({ATTR_FILE_LIST})

    _attr_has_entity_name = True
    entity_description: FolderSensorEntityDescription

    def __init__(
        self,
        coordinator: FolderCoordinator,
        entry: FolderConfigEntry,
        description: FolderSensorEntityDescription,
    ) -> None:
        """Initialize the data object."""
        super().__init__(coordinator)
        self.entity_description = description
        # The size sensor predates the other sensors and keeps the bare entry
        # id, so existing entities and their history survive an upgrade.
        self._attr_unique_id = (
            entry.entry_id
            if description.key == KEY_SIZE
            else f"{entry.entry_id}_{description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title or os.path.basename(coordinator.path),
        )

    @property
    def native_value(self) -> float | int:
        """Return the value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return the state attributes of the size sensor."""
        if self.entity_description.key != KEY_SIZE:
            return None

        data = self.coordinator.data
        return {
            ATTR_PATH: os.path.join(self.coordinator.path, ""),
            ATTR_FILTER: self.coordinator.filter_term,
            ATTR_NUMBER_OF_FILES: data.number_of_files,
            ATTR_BYTES: data.size,
            ATTR_FILE_LIST: data.files,
        }
