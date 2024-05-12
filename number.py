""" """

from homeassistant.components.number import DOMAIN as SENSOR_DOMAIN, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
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
    add_entities_callback([WaterTimerPauseDaysEntity(entry, device)], False)


class WaterTimerPauseDaysEntity(NumberEntity):
    """A setting to pause automatic watering for a number of days"""

    # _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_native_min_value = 0
    _attr_native_max_value = 7
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.DAYS

    def __init__(self, entry: ConfigEntry, device: WaterTimerDevice) -> None:
        self._dev = device
        self._config = entry
        self._integration_name = entry.title
        self._attr_value = 0
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}.{format_mac(self._dev.mac)}.pause-days"
        )

    @property
    def device_info(self):
        return self._dev.device_info

    @property
    def name(self):
        """Name of the entity."""
        return f"Pause days of {self._integration_name}"

    @property
    def unique_id(self) -> str:
        return f"{format_mac(self._dev.mac)}.pause-days"

    async def async_update(self) -> None:
        """Updates entity value"""
        await self._dev.update()
        self._attr_native_value = self._dev.pause_days

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._dev.available

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        await self._dev.set_pause_days(int(value))
