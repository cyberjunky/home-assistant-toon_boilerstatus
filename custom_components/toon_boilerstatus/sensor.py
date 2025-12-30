"""Support for reading Opentherm boiler status data using Toon thermostat's ketelmodule."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    SENSOR_MAP,
)
from .coordinator import ToonBoilerStatusCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapping from API response keys to our sensor keys
API_KEY_MAP = {
    "boilersetpoint": "boilerSetpoint",
    "boilerintemp": "boilerInTemp",
    "boilerouttemp": "boilerOutTemp",
    "boilerpressure": "boilerPressure",
    "boilermodulationlevel": "boilerModulationLevel",
    "roomtemp": "roomTemp",
    "roomtempsetpoint": "roomTempSetpoint",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Toon Boiler Status sensors from a config entry."""
    coordinator: ToonBoilerStatusCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create all available sensor entities
    entities = []
    for description in SENSOR_MAP.values():
        entities.append(
            ToonBoilerStatusSensor(
                coordinator=coordinator,
                description=description,
                entry=entry,
            )
        )
        _LOGGER.debug("Adding Toon Boiler Status sensor: %s", description.name)

    async_add_entities(entities)


class ToonBoilerStatusSensor(CoordinatorEntity[ToonBoilerStatusCoordinator], SensorEntity):
    """Representation of a Toon Boiler Status sensor."""

    def __init__(
        self,
        coordinator: ToonBoilerStatusCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        # Get device name from options (with fallback to data for migration)
        device_name = entry.options.get(CONF_NAME) or entry.data.get(CONF_NAME, DEFAULT_NAME)

        # Store for name property
        self._device_name = device_name

        # Set device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"{device_name} Boilerstatus",
            manufacturer="Eneco",
            model="Toon Thermostat",
            configuration_url=f"http://{coordinator.host}:{coordinator.port}",
        )

        # Set the entity name with device prefix (e.g., "Toon Boiler Modulation")
        self._attr_name = f"{device_name} {description.name}"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # Map our sensor key to the API response key
        api_key = API_KEY_MAP.get(self.entity_description.key)
        if not api_key:
            return None

        # Get the value from coordinator data
        value = self.coordinator.data.get(api_key)
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid value for %s: %s",
                self.entity_description.key,
                value,
            )
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attributes = {}

        if self.coordinator.data and "sampleTime" in self.coordinator.data:
            attributes["last_updated"] = self.coordinator.data["sampleTime"]

        return attributes
