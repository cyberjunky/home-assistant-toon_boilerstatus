"""Data update coordinator for Omnik Inverter."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SERIAL_NUMBER, DEFAULT_SCAN_INTERVAL, DOMAIN
from .omnik import OmnikConnectionError, OmnikInverter, OmnikInverterData

_LOGGER = logging.getLogger(__name__)


class OmnikDataUpdateCoordinator(DataUpdateCoordinator[OmnikInverterData]):
    """Class to manage fetching Omnik Inverter data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.inverter = OmnikInverter(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            serial_number=entry.data[CONF_SERIAL_NUMBER],
        )

        # Get scan interval from options, fall back to default
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> OmnikInverterData:
        """Fetch data from the inverter."""
        try:
            return await self.inverter.async_get_data()
        except OmnikConnectionError as err:
            raise UpdateFailed(f"Error communicating with inverter: {err}") from err
