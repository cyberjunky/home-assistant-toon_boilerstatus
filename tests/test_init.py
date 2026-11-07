"""Tests for Toon Boiler Status setup, unload and entity migration."""

from __future__ import annotations

import aiohttp
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.toon_boilerstatus.const import DOMAIN, SENSOR_KEYS

from .conftest import HOST, mock_toon


async def test_setup_and_unload_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """The entry loads, stores the coordinator, and unloads cleanly."""
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_setup_entry_not_ready(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """An unreachable Toon puts the entry in setup-retry."""
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock, exc=aiohttp.ClientError("boom"))

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_migrate_legacy_unique_ids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    entity_registry: er.EntityRegistry,
) -> None:
    """Pre-2.0 unique_ids ('Toon _<key>') are rewritten to '<entry_id>_<key>'."""
    mock_config_entry.add_to_hass(hass)
    key = SENSOR_KEYS[0]
    legacy = entity_registry.async_get_or_create(
        "sensor", DOMAIN, f"Toon _{key}", suggested_object_id=f"toon_{key}"
    )
    mock_toon(aioclient_mock)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    migrated = entity_registry.async_get(legacy.entity_id)
    assert migrated is not None
    assert migrated.unique_id == f"{mock_config_entry.entry_id}_{key}"
    assert migrated.config_entry_id == mock_config_entry.entry_id


async def test_yaml_import(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Domain-level YAML config is imported into a config entry."""
    mock_toon(aioclient_mock)

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {"sensor": [{"host": HOST}]}})
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].unique_id == HOST
