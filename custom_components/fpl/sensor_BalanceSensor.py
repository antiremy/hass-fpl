"""Balance sensors"""

from .fplEntity import FplMoneyEntity


class BalanceSensor(FplMoneyEntity):
    """balance sensor"""

    def __init__(self, coordinator, config, account):
        super().__init__(coordinator, config, account, "Balance Due")

    @property
    def native_value(self):
        self._attr_native_value = self.getData("balance")
        return self._attr_native_value

    def customAttributes(self):
        attributes = {"pastDue": self.getData("pastDue")}
        return attributes
