""" """

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    DOMAIN as SENSOR_DOMAIN,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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
    device = await create_device(hass, entry.data["mac"], entry.title)
    add_entities_callback(
        [WaterTimerRunningStatus(entry, device), WaterTimerAutoStatus(entry, device)],
        False,
    )


class WaterTimerRunningStatus(BinarySensorEntity):
    """_summary_

    :param BinarySensorEntity: _description_
    :type BinarySensorEntity: _type_
    """

    def __init__(self, entry: ConfigEntry, device: WaterTimerDevice) -> None:
        self._dev = device
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._integration_name = entry.title
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}.{format_mac(self._dev.mac)}.running-state"
        )

    @property
    def device_info(self):
        return self._dev.device_info

    @property
    def name(self):
        """Name of the entity."""
        return f"Running state of {self._integration_name}"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._dev.is_running

    @property
    def unique_id(self) -> str:
        return f"{format_mac(self._dev.mac)}.running-state"

    async def async_update(self) -> None:
        await self._dev.update()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._dev.available


class WaterTimerAutoStatus(BinarySensorEntity):
    def __init__(self, entry: ConfigEntry, device: WaterTimerDevice) -> None:
        self._dev = device
        self._attr_device_class = BinarySensorDeviceClass.MOVING
        self._integration_name = entry.title
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}.{format_mac(self._dev.mac)}.auto-mode-on"
        )

    @property
    def device_info(self):
        return self._dev.device_info

    @property
    def name(self):
        """Name of the entity."""
        return f"Auto mode state of {self._integration_name}"

    @property
    def is_on(self):
        """If the switch is currently on or off."""
        return self._dev.is_auto_mode_on

    @property
    def unique_id(self) -> str:
        return f"{format_mac(self._dev.mac)}.auto-mode-on"

    async def async_update(self) -> None:
        await self._dev.update()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._dev.available
