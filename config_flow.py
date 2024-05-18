"""Config flow for Spray-Mist-F638 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import format_mac

from .const import CONFIG_MANUAL_TIME, DOMAIN
from .device_wrapper import WaterTimerDevice

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required("mac"): str})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    ble_device = await bluetooth.async_ble_device_from_address(
        hass, data["mac"], connectable=True
    )
    if ble_device is None:
        _LOGGER.error("[Config flow] Cannot get the device with MAC %s", data["mac"])
    else:
        _LOGGER.info(
            "[Config flow] Got the device with MAC %s (%s)",
            data["mac"],
            ble_device.address,
        )
    device = WaterTimerDevice(ble_device if ble_device is not None else data["mac"], "")
    if not device.can_connect:
        raise CannotConnect

    # Return info that you want to store in the config entry.
    return {"title": f"WaterTimer {data['mac']}"}


class WaterTimerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spray-Mist-F638."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(format_mac(user_input["mac"]))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> WaterTimerOptionsFlowHandler:
        """Options callback for WaterTimer."""
        return WaterTimerOptionsFlowHandler(config_entry)


class WaterTimerOptionsFlowHandler(OptionsFlow):
    """Config flow options for WaterTimer."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize WaterTimer options flow."""
        self.config_entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONFIG_MANUAL_TIME,
                        default=self.config_entry.options.get(CONFIG_MANUAL_TIME, 30),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=120))
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
