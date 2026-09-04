"""Config flow for the Folder integration."""

from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_FILTER,
    CONF_FOLDER_PATHS,
    DEFAULT_FILTER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=MIN_SCAN_INTERVAL,
        max=MAX_SCAN_INTERVAL,
        step=1,
        mode=NumberSelectorMode.BOX,
        unit_of_measurement="s",
    )
)


def _normalise_path(path: str) -> str:
    """Expand and normalise a user supplied folder path."""
    return os.path.normpath(os.path.expanduser(path.strip()))


async def _async_validate_path(hass: HomeAssistant, path: str) -> str | None:
    """Return an error key if the folder cannot be used, otherwise None."""
    if not path:
        return "invalid_path"
    if not await hass.async_add_executor_job(os.path.isdir, path):
        return "not_dir"
    if not hass.config.is_allowed_path(path):
        return "not_allowed"
    return None


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the schema shown to the user."""
    return vol.Schema(
        {
            vol.Required(
                CONF_FOLDER_PATHS, default=defaults.get(CONF_FOLDER_PATHS, "")
            ): TextSelector(),
            vol.Optional(
                CONF_FILTER, default=defaults.get(CONF_FILTER, DEFAULT_FILTER)
            ): TextSelector(),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): SCAN_INTERVAL_SELECTOR,
        }
    )


class FolderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Folder."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a folder added by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            path = _normalise_path(user_input[CONF_FOLDER_PATHS])
            error = await _async_validate_path(self.hass, path)
            if error:
                errors[CONF_FOLDER_PATHS] = error
            else:
                self._async_abort_entries_match({CONF_FOLDER_PATHS: path})
                return self.async_create_entry(
                    title=os.path.basename(path) or path,
                    data={CONF_FOLDER_PATHS: path},
                    options={
                        CONF_FILTER: user_input.get(CONF_FILTER, DEFAULT_FILTER),
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                _user_schema({}), user_input or {}
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of an existing folder."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            path = _normalise_path(user_input[CONF_FOLDER_PATHS])
            error = await _async_validate_path(self.hass, path)
            if error:
                errors[CONF_FOLDER_PATHS] = error
            else:
                if path != entry.data[CONF_FOLDER_PATHS]:
                    self._async_abort_entries_match({CONF_FOLDER_PATHS: path})
                return self.async_update_reload_and_abort(
                    entry,
                    title=os.path.basename(path) or path,
                    data={CONF_FOLDER_PATHS: path},
                    options={
                        CONF_FILTER: user_input.get(CONF_FILTER, DEFAULT_FILTER),
                        CONF_SCAN_INTERVAL: int(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        ),
                    },
                )

        suggested = {
            CONF_FOLDER_PATHS: entry.data[CONF_FOLDER_PATHS],
            CONF_FILTER: entry.options.get(CONF_FILTER, DEFAULT_FILTER),
            CONF_SCAN_INTERVAL: entry.options.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            ),
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _user_schema(suggested), user_input or suggested
            ),
            errors=errors,
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Import a folder sensor configured in YAML."""
        path = _normalise_path(import_data[CONF_FOLDER_PATHS])
        error = await _async_validate_path(self.hass, path)
        if error:
            _LOGGER.error("Unable to import folder %s: %s", path, error)
            return self.async_abort(reason=error)

        self._async_abort_entries_match({CONF_FOLDER_PATHS: path})
        return self.async_create_entry(
            title=os.path.basename(path) or path,
            data={CONF_FOLDER_PATHS: path},
            options={
                CONF_FILTER: import_data.get(CONF_FILTER, DEFAULT_FILTER),
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> FolderOptionsFlow:
        """Get the options flow for this handler."""
        return FolderOptionsFlow()


class FolderOptionsFlow(OptionsFlow):
    """Handle options for a configured folder."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the filter and polling interval."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_FILTER: user_input.get(CONF_FILTER, DEFAULT_FILTER),
                    CONF_SCAN_INTERVAL: int(
                        user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ),
                }
            )

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FILTER, default=options.get(CONF_FILTER, DEFAULT_FILTER)
                ): TextSelector(),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): SCAN_INTERVAL_SELECTOR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
