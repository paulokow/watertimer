""" """

from homeassistant.components.switch import (
    DOMAIN as SENSOR_DOMAIN,
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONFIG_MANUAL_TIME, DOMAIN
from .device_wrapper import WaterTimerDevice, create_device


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, add_entities_callback: AddEntitiesCallback
) -> None:
    """Function which is called by HAAS to setup entities of this platform

    :param hass: reference to HASS
    :type hass: HomeAssistant
    :param entry: configuration
    :type entry: ConfigEntry
    :param add_entities_callback: callback function to add entities
    :type add_entities_callback: AddEntitiesCallback
    :return: success
    :rtype: bool
    """
    device = create_device(entry.data["mac"], entry.title)
    add_entities_callback([WaterTimerManualSwitch(entry, device)], False)


class WaterTimerManualSwitch(SwitchEntity):
    """A switch for turning water timer on and off"""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, entry: ConfigEntry, device: WaterTimerDevice) -> None:
        self._dev = device
        self._config = entry
        self._integration_name = entry.title
        self._manual_mode_time = entry.options.get(CONFIG_MANUAL_TIME, 30)
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}.{format_mac(self._dev.mac)}.manual-switch"
        )

    @property
    def device_info(self):
        return self._dev.device_info

    @property
    def name(self):
        """Name of the entity."""
        return f"Manual switch of {self._integration_name}"

    @property
    def unique_id(self) -> str:
        return f"{format_mac(self._dev.mac)}.manual-switch"

    async def async_update(self) -> None:
        await self._dev.update()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._dev.available

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self._dev.turn_manual_on(
            self.platform.config_entry.options.get(CONFIG_MANUAL_TIME, 0)
            if self.platform is not None and self.platform.config_entry is not None
            else 0
        )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self._dev.turn_manual_off()

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._dev.manual_mode_on
