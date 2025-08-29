"""Data Update Coordinator"""

import logging
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.core import HomeAssistant


from .fplapi import FplApi
from .const import DOMAIN, CONF_ACCOUNTS

SCAN_INTERVAL = timedelta(seconds=1200)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class FplDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: FplApi) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    def _publish_hourly_statistics(self, account: str, hourly: list) -> None:
        base_metadata = {
            "has_mean": False,
            "has_sum": True,
            "source": DOMAIN,
        }

        cost_stats = []
        usage_stats = []
        for h in hourly:
            cost = h.get("billingCharged")
            usage = h.get("kwhActual")
            read_time = h.get("readTime")
            if read_time is None:
                continue
            start = read_time - timedelta(hours=1)
            if cost is not None:
                cost_stats.append({"start": start, "sum": float(cost)})
            if usage is not None:
                usage_stats.append({"start": start, "sum": float(usage)})

        if cost_stats:
            metadata = base_metadata.copy()
            metadata["name"] = f"FPL {account} Hourly Cost"
            metadata["statistic_id"] = f"{DOMAIN}:{account}:hourly_cost"
            metadata["unit_of_measurement"] = "USD"

            async_add_external_statistics(self.hass, metadata, cost_stats)

        if usage_stats:
            metadata = base_metadata.copy()
            metadata["name"] = f"FPL {account} Hourly Usage"
            metadata["statistic_id"] = f"{DOMAIN}:{account}:hourly_usage"
            metadata["unit_of_measurement"] = "kWh"

            async_add_external_statistics(self.hass, metadata, usage_stats)

    async def _async_update_data(self):
        try:
            data = await self.api.async_get_data()

            # Backfill hourly cost for accounts (align to each hour)
            for account in data.get(CONF_ACCOUNTS, []):
                hourly = data.get(account, {}).get("HourlyUsage")
                if hourly:
                    try:
                        self._publish_hourly_statistics(account, hourly)
                    except Exception as e:
                        _LOGGER.error(f"Error publishing hourly statistics for account {account}: {e}")

            return data
        except Exception as exception:
            raise UpdateFailed() from exception
