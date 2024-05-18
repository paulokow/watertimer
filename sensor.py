""" """

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
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
    device = create_device(hass, entry.data["mac"], entry.title)
    add_entities_callback(
        [
            WaterTimerBatteryStatus(entry, device),
            WaterTimerManualModeTime(entry, device),
        ],
        False,
    )


class WaterTimerBatteryStatus(SensorEntity):
    """_summary_

    :param BinarySensorEntity: _description_
    :type BinarySensorEntity: _type_
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, entry: ConfigEntry, device: WaterTimerDevice) -> None:
        self._dev = device
        self._integration_name = entry.title
        self.entity_id = f"{SENSOR_DOMAIN}.{DOMAIN}.{format_mac(self._dev.mac)}.battery"

    @property
    def device_info(self):
        return self._dev.device_info

    @property
    def name(self):
        """Name of the entity."""
        return f"Battery level of {self._integration_name}"

    @property
    def unique_id(self) -> str:
        return f"{format_mac(self._dev.mac)}.battery"

    async def async_update(self) -> None:
        await self._dev.update()
        self._attr_native_value = self._dev.battery_level

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._dev.available


class WaterTimerManualModeTime(SensorEntity):
    """_summary_

    :param BinarySensorEntity: _description_
    :type BinarySensorEntity: _type_
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:clock-end"

    def __init__(self, entry: ConfigEntry, device: WaterTimerDevice) -> None:
        self._dev = device
        self._integration_name = entry.title
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{DOMAIN}.{format_mac(self._dev.mac)}.manual-mode-minutes"
        )

    @property
    def device_info(self):
        return self._dev.device_info

    @property
    def name(self):
        """Name of the entity."""
        return f"Manual mode minutes of {self._integration_name}"

    @property
    def unique_id(self) -> str:
        return f"{format_mac(self._dev.mac)}.manual-mode-minutes"

    async def async_update(self) -> None:
        await self._dev.update()
        self._attr_native_value = (
            self._dev.manual_mode_time
            if self._dev.manual_mode_on
            else (
                self.platform.config_entry.options.get(CONFIG_MANUAL_TIME, 0)
                if self.platform is not None and self.platform.config_entry is not None
                else 0
            )
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._dev.available
