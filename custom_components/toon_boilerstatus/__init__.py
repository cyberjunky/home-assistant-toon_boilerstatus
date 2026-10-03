"""Toon Boiler Status integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SENSOR_KEYS,
)
from .coordinator import ToonBoilerStatusCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

# Schema for YAML configuration (legacy support for migration)
SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("sensor"): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_migrate_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Migrate pre-2.0 entities to the current unique_id format.

    Pre-2.0 releases built the unique_id from the YAML name and the sensor key,
    e.g. unique_id="Toon _boilersetpoint" for the default name "Toon ".
    Renaming the unique_id lets the entity registry reuse the existing
    entity_id, so history and long-term statistics are kept.
    """
    entity_registry = er.async_get(hass)
    host = entry.data.get(CONF_HOST)
    name = entry.options.get(CONF_NAME) or entry.data.get(CONF_NAME, DEFAULT_NAME)
    # The old default name had a trailing space, which YAML strips unless quoted
    legacy_prefixes = dict.fromkeys((name, f"{name} ", "Toon ", "Toon"))
    migrated_count = 0

    for sensor_key in SENSOR_KEYS:
        new_unique_id = f"{entry.entry_id}_{sensor_key}"

        # Already migrated / already on the new scheme.
        if entity_registry.async_get_entity_id("sensor", DOMAIN, new_unique_id):
            continue

        for prefix in legacy_prefixes:
            old_unique_id = f"{prefix}_{sensor_key}"
            entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, old_unique_id)
            if not entity_id:
                continue

            _LOGGER.info(
                "Migrating entity %s from legacy unique_id '%s' to '%s'",
                entity_id,
                old_unique_id,
                new_unique_id,
            )
            entity_registry.async_update_entity(
                entity_id,
                new_unique_id=new_unique_id,
                config_entry_id=entry.entry_id,
            )
            migrated_count += 1
            break

    if migrated_count > 0:
        _LOGGER.info("Migrated %s entities for host %s", migrated_count, host)
    else:
        _LOGGER.debug("No legacy entities found to migrate for host %s", host)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Toon Boiler Status integration from YAML (legacy migration)."""
    hass.data.setdefault(DOMAIN, {})

    # Check for legacy sensor platform configuration
    if "sensor" in config:
        for platform_config in config["sensor"]:
            if platform_config.get("platform") == DOMAIN:
                _LOGGER.warning(
                    "Configuration of Toon Boiler Status via YAML platform is deprecated. "
                    "Your configuration has been imported. Please remove the YAML "
                    "configuration and restart Home Assistant."
                )
                # Import the configuration
                hass.async_create_task(
                    hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": "import"},
                        data=platform_config,
                    )
                )

    # Check for new-style domain configuration
    if DOMAIN in config:
        domain_config = config[DOMAIN]
        if "sensor" in domain_config:
            for sensor_config in domain_config["sensor"]:
                _LOGGER.warning(
                    "Configuration of Toon Boiler Status via YAML is deprecated. "
                    "Your configuration has been imported. Please remove the YAML "
                    "configuration and restart Home Assistant."
                )
                hass.async_create_task(
                    hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": "import"},
                        data=sensor_config,
                    )
                )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Toon Boiler Status from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Migrate old entities to new unique_id format
    await async_migrate_entities(hass, entry)

    session = async_get_clientsession(hass)

    # Get configuration - host/port from data, user preferences from options
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create coordinator
    coordinator = ToonBoilerStatusCoordinator(
        hass=hass,
        session=session,
        host=host,
        port=port,
        scan_interval=scan_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)

    # Currently at version 1, so no migration needed yet
    # This is a placeholder for future migrations
    if entry.version == 1:
        # No migration needed
        pass

    _LOGGER.info("Migration to version %s successful", entry.version)
    return True
