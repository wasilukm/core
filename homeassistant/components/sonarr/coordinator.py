"""Coordinator for Sonarr."""
from __future__ import annotations

from datetime import timedelta
import logging

from sonarr import Sonarr, SonarrError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)
_LOGGER = logging.getLogger(__name__)


class SonarrDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching Sonarr data."""

    sonarr: Sonarr
    datapoints: list
    upcoming_days: int

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        sonarr: Sonarr,
        upcoming_days: int = 1,
    ) -> None:
        """Initialize global Sonarr data updater."""
        self.sonarr = sonarr
        self.upcoming_days = upcoming_days

        self.datapoints = ["app"]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    def enable_datapoint(self, datapoint: str):
        """Enable collection of a datapoint from its respective endpoint."""
        self.datapoints.push(datapoint)

    async def get_datapoint(self, datapoint: str):
        """Fetch datapoint from its respective endpoint."""
        if datapoint == "app":
            return self.sonarr.update()
        elif datapoint == "commands":
            return self.sonarr.commands()
        elif datapoint == "queue":
            return self.sonarr.queue()
        elif datapoint == "series":
            return self.sonarr.series()
        elif datapoint == "upcoming":
            local = dt_util.start_of_local_day().replace(microsecond=0)
            start = dt_util.as_utc(local)
            end = start + timedelta(days=self.upcoming_days)

            return self.sonarr.upcoming(
                start=start.isoformat(), end=end.isoformat()
            )
        elif datapoint == "wanted":
            return self.sonarr.wanted()

        return None

    async def _async_update_data(self) -> dict:
        """Fetch data from Sonarr."""
        try: 
            data = dict(
                zip(
                    self.datapoints,
                    await asyncio.gather(
                        *(self.get_datapoint(datapoint) for datapoint in self.datapoints),
                    ),
                )
            )

            return data
        except SonarrError as error:
            raise UpdateFailed(f"Invalid response from API: {error}") from error
