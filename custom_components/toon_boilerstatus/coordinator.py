"""Data coordinator for Toon Boiler Status integration."""

import logging
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ToonBoilerStatusCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Toon boiler status data."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.host = host
        self.port = port
        self._session = session
        self._url = BASE_URL.format(host, port)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Toon device."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    self._url, headers={"Accept-Encoding": "identity"}
                )
                response.raise_for_status()
                data = await response.json(content_type="text/plain")
                _LOGGER.debug("Data received from Toon: %s", data)
                return data
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Toon at {self._url}: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout fetching data from {self._url}") from err
        except (TypeError, KeyError, ValueError) as err:
            raise UpdateFailed(f"Error parsing Toon data: {err}") from err
