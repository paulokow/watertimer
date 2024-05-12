from datetime import datetime, timedelta
import logging
from random import randint
from threading import RLock
from time import sleep
from typing import Union

from spraymistf638.driver import RunningMode, SprayMistF638, WorkingMode

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

updatelock = RLock()

if _LOGGER.isEnabledFor(logging.DEBUG):
    from unittest.mock import Mock, PropertyMock

    manual_mode = False
    pause_days = randint(0, 7)

    def switch_manual_on(t):
        _LOGGER.debug("Water timer switched on for %s", t)
        global manual_mode
        manual_mode = True

    def switch_manual_off():
        _LOGGER.debug("Water timer switched off")
        global manual_mode
        manual_mode = False

    def set_pause_days(val: int):
        _LOGGER.debug(f"Pause days set to {val}")
        global pause_days
        pause_days = val

    SprayMistF638 = Mock(spec=SprayMistF638)
    SprayMistF638.return_value.connect = Mock(side_effect=lambda: randint(0, 3) != 0)
    type(SprayMistF638.return_value).running_mode = PropertyMock(
        side_effect=lambda: randint(0, 3)
    )
    type(SprayMistF638.return_value).working_mode = PropertyMock(
        side_effect=lambda: randint(0, 1)
    )
    type(SprayMistF638.return_value).battery_level = PropertyMock(
        side_effect=lambda: randint(1, 100)
    )
    type(SprayMistF638.return_value).manual_on = PropertyMock(
        side_effect=lambda: manual_mode
    )
    type(SprayMistF638.return_value).manual_time = PropertyMock(
        side_effect=lambda: randint(1, 100)
    )
    type(SprayMistF638.return_value).pause_days = PropertyMock(
        side_effect=lambda: pause_days
    )
    SprayMistF638.return_value.switch_manual_on = Mock(side_effect=switch_manual_on)
    SprayMistF638.return_value.switch_manual_off = Mock(side_effect=switch_manual_off)
    SprayMistF638.return_value.set_pause_days = Mock(side_effect=set_pause_days)
    _LOGGER.warning("Device is mocked in debug logging mode")


class WaterTimerDevice:
    """AI is creating summary for"""

    def __init__(self, mac: str, name: str) -> None:
        self._mac = mac
        self._last_update = datetime.min
        self._name = name
        self._is_available = False
        self._is_running = False
        self._battery_level = None
        self._auto_mode_on = False
        self._manual_mode_time = 30
        self._manual_mode_on = False
        self._pause_days = 0
        self._device_handle = SprayMistF638(mac)

    @property
    def device_info(self) -> dict:
        """Generate device info structure

        :return: device info
        :rtype: dict[str, str]
        """
        return {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            # "manufacturer": self.light.manufacturername,
            # "model": self.light.productname,
            # "sw_version": self.light.swversion,
            # "via_device": (hue.DOMAIN, self.api.bridgeid),
        }

    def update(self, force: bool = False):
        """Updates device, not more frequent than once / minute"""
        _LOGGER.debug("Update called")
        now = datetime.now()
        with updatelock:
            if now - self._last_update > timedelta(minutes=1) or force:
                self._perform_update()
                self._last_update = now

    def _perform_update(self):
        """Performs actual update of the device data"""
        _LOGGER.debug("..Performing update")
        try:
            connected = False
            for i in range(1, 6):
                connected = self._device_handle.connect()
                if connected:
                    break
                else:
                    _LOGGER.info(
                        "Water timer device: %s not connected retry %d",
                        self._mac,
                        i,
                    )
                    sleep(1)
            if connected:
                self._is_available = True
                self._is_running = self._device_handle.running_mode in [
                    RunningMode.RunningAutomatic,
                    RunningMode.RunningManual,
                ]
                self._auto_mode_on = (
                    self._device_handle.working_mode == WorkingMode.Auto
                )
                self._battery_level = int(self._device_handle.battery_level)
                self._manual_mode_time = self._device_handle.manual_time
                self._manual_mode_on = self._device_handle.manual_on
                self._pause_days = self._device_handle.pause_days
            else:
                _LOGGER.warning("Water timer device: %s cannot be reached", self._mac)
                self._is_available = False
        finally:
            self._device_handle.disconnect()

    @property
    def mac(self) -> str:
        """Returns the MAC address

        :return: MAC address of the device
        :rtype: str
        """
        return self._mac

    @property
    def can_connect(self) -> bool:
        """Checks connection to the device

        :return: if connection was successful
        :rtype: bool
        """
        _LOGGER.debug("Reading can_connect")
        ret = False
        try:
            ret = self._device_handle.connect()
        finally:
            self._device_handle.disconnect()
        return ret

    @property
    def is_running(self) -> bool:
        """Checks if the device is active at the moment

        :return: Active state
        :rtype: bool
        """
        _LOGGER.debug("Reading is_running")
        return self._is_running

    @property
    def is_running_in_manual_mode(self) -> bool:
        """Checks if the device is active at the moment

        :return: Active state
        :rtype: bool
        """
        _LOGGER.debug("Reading is_running")
        return self._is_running

    @property
    def is_auto_mode_on(self) -> bool:
        """Checks if automated mode is on

        :return: Auto mode state
        :rtype: bool
        """
        _LOGGER.debug("Reading auto_mode")
        return self._auto_mode_on

    @property
    def available(self) -> bool:
        """Reports if the device is connected

        :return: if the device is available
        :rtype: bool
        """
        _LOGGER.debug("Reading availability")
        return self._is_available

    @property
    def battery_level(self) -> Union[int, None]:
        """Reports the device battery level in %

        :return: battery level %
        :rtype: int
        """
        _LOGGER.debug("Reading battery level")
        return self._battery_level

    @property
    def manual_mode_on(self) -> bool:
        """Reports the manual mode status

        :return: if manual mode is started
        :rtype: bool
        """
        _LOGGER.debug("Reading manual mode on")
        return self._manual_mode_on

    def turn_manual_on(self, time: int = 0) -> bool:
        """Turn on device in manual mode

        :param time: Run duration, zero means last default value, defaults to 0
        :type time: int, optional
        :return: if function succeeded
        :rtype: bool
        """
        ret = False
        with updatelock:
            try:
                ret = self._device_handle.switch_manual_on(time)
                self.update(force=True)
            finally:
                self._device_handle.disconnect()
        return ret

    def turn_manual_off(self) -> bool:
        """Turn off device in manual mode

        :return: if function succeeded
        :rtype: bool
        """
        ret = False
        with updatelock:
            try:
                ret = self._device_handle.switch_manual_off()
                self.update(force=True)
            finally:
                self._device_handle.disconnect()
        return ret

    @property
    def manual_mode_time(self) -> int:
        """Reports the manual mode time (set or remaining) in minutes

        :return: set time (if off) or remaining time (if on) for manual mode run
        :rtype: int
        """
        _LOGGER.debug("Reading manual mode time")
        return self._manual_mode_time

    @property
    def pause_days(self) -> int:
        """Reports pause days

        :return: value
        :rtype: int
        """
        _LOGGER.debug("Reading pause days")
        return self._pause_days

    def set_pause_days(self, value: int) -> bool:
        """Setting for pause days

        :param value: Pause duration in days
        :type value: int
        :return: if function succeeded
        :rtype: bool
        """
        _LOGGER.debug(f"Setting pause days: {value}")
        ret = False
        with updatelock:
            try:
                ret = self._device_handle.set_pause_days(value)
                self.update(force=True)
            finally:
                self._device_handle.disconnect()
        return ret


devices: dict[str, WaterTimerDevice] = dict()


def create_device(mac: str, name: str) -> WaterTimerDevice:
    """Creates a WaterTimer device object or returns an existing one by mac address

    :param mac: mac address
    :type mac: str
    :param name: name of the device to create
    :type name: str
    :return: created or existing device object
    :rtype: WaterTimerDevice
    """
    if mac in devices:
        return devices[mac]
    else:
        dev = WaterTimerDevice(mac, name)
        devices[mac] = dev
        return dev
