"""Average daily sensors"""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from .fplEntity import FplMoneyEntity, FplEnergyEntity

from datetime import datetime


class ApplianceCostSensor(FplMoneyEntity):
    """Appliance Cost Sensor"""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    APPLIANCE_NAME = None

    def __init__(self, coordinator, config, account):
        assert self.APPLIANCE_NAME is not None, "APPLIANCE_NAME must be set"
        super().__init__(coordinator, config, account, f"{self.APPLIANCE_NAME} Cost")

    @property
    def native_value(self):
        appliance_usage = self.getData("appliance_usage")
        categories = appliance_usage.get("categories")
        for category in categories:
            if category.get("category") == self.APPLIANCE_NAME:
                self._attr_native_value = category.get("cost")
                return self._attr_native_value

    def customAttributes(self):
        """Return the state attributes."""
        # Add any extra attributes you want to expose here
        appliance_usage = self.getData("appliance_usage")
        attributes = {
            "startDate": datetime.strptime(appliance_usage.get("startDate"), "%Y-%m-%d").strftime("%Y-%m-%d"),
            "endDate": datetime.strptime(appliance_usage.get("endDate"), "%Y-%m-%d").strftime("%Y-%m-%d"),
        }
        return attributes
    

class ApplianceUsageSensor(FplEnergyEntity):
    """Appliance Usage Sensor in KWH"""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL

    APPLIANCE_NAME = None

    def __init__(self, coordinator, config, account):
        assert self.APPLIANCE_NAME is not None, "APPLIANCE_NAME must be set"
        super().__init__(coordinator, config, account, f"{self.APPLIANCE_NAME} Usage kWh")

    @property
    def native_value(self):
        appliance_usage = self.getData("appliance_usage")
        categories = appliance_usage.get("categories")
        for category in categories:
            if category.get("category") == self.APPLIANCE_NAME:
                self._attr_native_value = category.get("kwh")
                return self._attr_native_value

    def customAttributes(self):
        """Return the state attributes."""
        # Add any extra attributes you want to expose here
        appliance_usage = self.getData("appliance_usage")
        attributes = {
            "startDate": datetime.strptime(appliance_usage.get("startDate"), "%Y-%m-%d").strftime("%Y-%m-%d"),
            "endDate": datetime.strptime(appliance_usage.get("endDate"), "%Y-%m-%d").strftime("%Y-%m-%d"),
        }
        return attributes
    

class CoolingCostSensor(ApplianceCostSensor):
    """Cooling Cost Sensor"""

    APPLIANCE_NAME = "cooling"

class CoolingUsageSensor(ApplianceUsageSensor):
    """Cooling Usage Sensor in KWH"""

    APPLIANCE_NAME = "cooling"