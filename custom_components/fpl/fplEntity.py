"""Fpl Entity class"""
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.const import (
    CURRENCY_DOLLAR,
    ENERGY_KILO_WATT_HOUR,
)
from .const import DOMAIN, VERSION, ATTRIBUTION


class FplEntity(CoordinatorEntity, SensorEntity):
    """FPL base entity"""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator, config_entry, account, sensorName):
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.account = account
        self.sensorName = sensorName

    @property
    def unique_id(self):
        """Return the ID of this device."""
        sensorName = self.sensorName.lower().replace(" ", "")
        return f"{DOMAIN}{self.account}{sensorName}"

    @property
    def name(self):
        return f"{DOMAIN.upper()} {self.account} {self.sensorName}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.account)},
            "name": f"FPL {self.account}",
            "model": VERSION,
            "manufacturer": "Florida Power & Light",
            "configuration_url": "https://www.fpl.com/my-account/residential-dashboard.html",
        }

    def customAttributes(self) -> dict:
        """Override this method to set custom attributes."""
        return {}

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {"attribution": ATTRIBUTION}
        attributes.update(self.customAttributes())
        return attributes

    def getData(self, field):
        """Call this method to retrieve sensor data."""
        if self.coordinator.data is not None:
            account = self.coordinator.data.get(self.account)
            if account is not None:
                return account.get(field, None)
        return None


class FplEnergyEntity(FplEntity):
    """Represents an energy sensor (kWh)."""

    _attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_icon = "mdi:flash"

    @property
    def last_reset_not_use(self) -> datetime:
        """Example method if you ever need a daily reset time."""
        today = datetime.today()
        yesterday = today - timedelta(days=1)
        return datetime.combine(yesterday, datetime.min.time())


class FplMoneyEntity(FplEntity):
    """Represents a money sensor ($)."""

    # You may replace this with "USD" if you prefer:
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_icon = "mdi:currency-usd"


class FplDateEntity(FplEntity):
    """Represents a date or days."""

    _attr_icon = "mdi:calendar"


class FplDayEntity(FplEntity):
    """Represents a sensor measured in days."""

    _attr_native_unit_of_measurement = "days"
    _attr_icon = "mdi:calendar"
