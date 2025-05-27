"""Hourly Usage Sensors"""

# Modern imports:
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass


from .fplEntity import FplEnergyEntity, FplMoneyEntity


class FplHourlyUsageSensor(FplMoneyEntity):
    """Hourly Usage Cost Sensor (monetary)"""

    # If this cost is just for the current hour and resets each hour,
    # consider using SensorStateClass.MEASUREMENT.
    # If it's a cumulative cost that keeps increasing, consider TOTAL_INCREASING.
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Hourly Usage")

    @property
    def native_value(self):
        data = self.getData("hourly_usage")
        if data and len(data) > 0 and "cost" in data[-1]:
            self._attr_native_value = data[-1]["cost"]
        return self._attr_native_value

    def customAttributes(self):
        """Return any additional attributes."""
        data = self.getData("hourly_usage")
        attributes = {}
        if data and len(data) > 0 and "readTime" in data[-1]:
            attributes["date"] = data[-1]["readTime"]
        return attributes


class FplHourlyUsageKWHSensor(FplEnergyEntity):
    """Hourly Usage KWh Sensor"""

    # Decide if this is cumulative (TOTAL / TOTAL_INCREASING)
    # or a per-hour reading that resets each hour (MEASUREMENT).
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Hourly Usage KWH")

    @property
    def statistic_id(self) -> str:
        """Optional statistic_id for advanced stats/energy dashboard."""
        return self.entity_id

    # Uncomment and adapt if you want to return a reading from the coordinator:
    #
    # @property
    # def native_value(self):
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "kwhActual" in data[-1]:
    #         self._attr_native_value = data[-1]["kwhActual"]
    #     return self._attr_native_value
    #
    # @property
    # def last_reset(self) -> datetime | None:
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "readTime" in data[-1]:
    #         return data[-1]["readTime"]  # or data[-1]["readTime"] - timedelta(hours=1)
    #     return None

    def customAttributes(self):
        return {}


class FplHourlyReceivedKWHSensor(FplEnergyEntity):
    """Hourly Received KWh Sensor"""

    # If you’re tracking an hourly usage that resets each hour, use MEASUREMENT or TOTAL.
    # If it's a continuously growing total, use TOTAL_INCREASING.
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Hourly Received KWH")

    @property
    def statistic_id(self) -> str:
        return self.entity_id

    # Uncomment if you want to provide a reading:
    #
    # @property
    # def native_value(self):
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "netReceived" in data[-1]:
    #         self._attr_native_value = data[-1]["netReceived"]
    #     return self._attr_native_value
    #
    # @property
    # def last_reset(self) -> datetime | None:
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "readTime" in data[-1]:
    #         return data[-1]["readTime"]
    #     return None

    def customAttributes(self):
        return {}


class FplHourlyDeliveredKWHSensor(FplEnergyEntity):
    """Hourly Delivered KWh Sensor"""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Hourly Delivered KWH")

    # @property
    # def native_value(self):
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "netDelivered" in data[-1]:
    #         self._attr_native_value = data[-1]["netDelivered"]
    #     return self._attr_native_value
    #
    # @property
    # def last_reset(self) -> datetime | None:
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "readTime" in data[-1]:
    #         return data[-1]["readTime"]
    #     return None

    def customAttributes(self):
        return {}


class FplHourlyReadingKWHSensor(FplEnergyEntity):
    """Hourly Reading KWh Sensor (Meter)"""

    # If this reading is a continuously increasing meter, use TOTAL_INCREASING.
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Hourly reading KWH")

    # @property
    # def native_value(self):
    #     data = self.getData("hourly_usage")
    #     if data and len(data) > 0 and "reading" in data[-1]:
    #         self._attr_native_value = data[-1]["reading"]
    #     return self._attr_native_value

    def customAttributes(self):
        return {}
