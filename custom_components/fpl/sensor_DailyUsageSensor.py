"""Daily Usage Sensors"""
from datetime import timedelta, datetime

# Updated imports:
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)

from .fplEntity import FplEnergyEntity, FplMoneyEntity


class FplDailyUsageSensor(FplMoneyEntity):
    """Daily Usage Cost Sensor (monetary)"""

    # If this sensor represents the cost *just for today* (not cumulative),
    # then use MEASUREMENT. If it's a cumulative total cost so far, use TOTAL_INCREASING.
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Daily Usage")

    @property
    def native_value(self):
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "cost" in data[-1]:
            self._attr_native_value = data[-1]["cost"]
        return self._attr_native_value

    def customAttributes(self):
        """Return the state attributes."""
        data = self.getData("daily_usage")
        attributes = {}

        if data and len(data) > 0 and "readTime" in data[-1]:
            attributes["date"] = data[-1]["readTime"]

        return attributes


class FplDailyUsageKWHSensor(FplEnergyEntity):
    """Daily Usage KWH Sensor"""

    # For daily usage, you might choose TOTAL if it's the total for that day
    # or TOTAL_INCREASING if you're incrementing throughout the day.
    _attr_state_class = SensorStateClass.TOTAL
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Daily Usage KWH")

    @property
    def native_value(self):
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "usage" in data[-1]:
            self._attr_native_value = data[-1]["usage"]
        return self._attr_native_value

    @property
    def last_reset(self) -> datetime | None:
        """An optional last_reset property for daily totals."""
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "usage" in data[-1]:
            date = data[-1]["readTime"]
            return date - timedelta(days=1)
        return None

    def customAttributes(self):
        """Return any additional attributes."""
        # Example: date or other details if needed
        return {}


class FplDailyReceivedKWHSensor(FplEnergyEntity):
    """Daily Received KWH Sensor"""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Daily Received KWH")

    @property
    def native_value(self):
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "netReceivedKwh" in data[-1]:
            self._attr_native_value = data[-1]["netReceivedKwh"]
        return self._attr_native_value

    @property
    def last_reset(self) -> datetime | None:
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "netReceivedKwh" in data[-1]:
            date = data[-1]["readTime"]
            return date - timedelta(days=1)
        return None

    def customAttributes(self):
        """Return any additional attributes."""
        data = self.getData("daily_usage")
        attributes = {}
        if data and len(data) > 0 and "readTime" in data[-1]:
            attributes["date"] = data[-1]["readTime"]
        return attributes


class FplDailyDeliveredKWHSensor(FplEnergyEntity):
    """Daily Delivered KWH Sensor"""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Daily Delivered KWH")

    @property
    def native_value(self):
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "netDeliveredKwh" in data[-1]:
            self._attr_native_value = data[-1]["netDeliveredKwh"]
        return self._attr_native_value

    @property
    def last_reset(self) -> datetime | None:
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "netDeliveredKwh" in data[-1]:
            date = data[-1]["readTime"]
            return date - timedelta(days=1)
        return None

    def customAttributes(self):
        """Return any additional attributes."""
        data = self.getData("daily_usage")
        attributes = {}
        if data and len(data) > 0 and "readTime" in data[-1]:
            attributes["date"] = data[-1]["readTime"]
        return attributes


class FplDailyReceivedReading(FplEnergyEntity):
    """Daily Received Reading (Meter)"""

    # If this reading is continuously increasing, TOTAL_INCREASING is correct:
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Daily Received reading")

    @property
    def native_value(self):
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "netReceivedReading" in data[-1]:
            self._attr_native_value = data[-1]["netReceivedReading"]
        return self._attr_native_value


class FplDailyDeliveredReading(FplEnergyEntity):
    """Daily Delivered Reading (Meter)"""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Daily Delivered reading")

    @property
    def native_value(self):
        data = self.getData("daily_usage")
        if data and len(data) > 0 and "netDeliveredReading" in data[-1]:
            self._attr_native_value = data[-1]["netDeliveredReading"]
        return self._attr_native_value
