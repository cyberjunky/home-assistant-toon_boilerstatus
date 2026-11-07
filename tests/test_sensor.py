"""Tests for Toon Boiler Status sensors."""

from __future__ import annotations

from datetime import timedelta

import aiohttp
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.toon_boilerstatus.const import DOMAIN, SENSOR_KEYS

from .conftest import MOCK_DATA, mock_toon

EXPECTED = {
    "boilersetpoint": "55.0",
    "boilerintemp": "40.5",
    "boilerouttemp": "52.25",
    "boilerpressure": "1.6",
    "boilermodulationlevel": "30.0",
    "roomtemp": "20.5",
    "roomtempsetpoint": "21.0",
}


def _entity_id(entity_registry: er.EntityRegistry, entry: MockConfigEntry, key: str) -> str:
    entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{key}")
    assert entity_id is not None, key
    return entity_id


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_sensors_created_with_values(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    entity_registry: er.EntityRegistry,
) -> None:
    """Every sensor is created and reports the mapped API value as float."""
    mock_toon(aioclient_mock)
    await _setup(hass, mock_config_entry)

    assert set(EXPECTED) == set(SENSOR_KEYS)
    for key, expected in EXPECTED.items():
        state = hass.states.get(_entity_id(entity_registry, mock_config_entry, key))
        assert state is not None, key
        assert state.state == expected, key
        assert state.attributes["last_updated"] == MOCK_DATA["sampleTime"]


async def test_sensor_missing_and_invalid_values(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    entity_registry: er.EntityRegistry,
) -> None:
    """Missing keys and non-numeric values yield an unknown state."""
    data = {**MOCK_DATA, "roomTemp": "n/a"}
    del data["boilerPressure"]
    mock_toon(aioclient_mock, data)
    await _setup(hass, mock_config_entry)

    room = hass.states.get(_entity_id(entity_registry, mock_config_entry, "roomtemp"))
    pressure = hass.states.get(_entity_id(entity_registry, mock_config_entry, "boilerpressure"))
    assert room.state == STATE_UNKNOWN
    assert pressure.state == STATE_UNKNOWN


async def test_sensor_unavailable_on_update_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    entity_registry: er.EntityRegistry,
) -> None:
    """A failing poll marks sensors unavailable; recovery restores them."""
    mock_toon(aioclient_mock)
    await _setup(hass, mock_config_entry)
    entity_id = _entity_id(entity_registry, mock_config_entry, "roomtemp")

    mock_toon(aioclient_mock, exc=aiohttp.ClientError("boom"))
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    mock_toon(aioclient_mock, {**MOCK_DATA, "roomTemp": 19.0})
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=22))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "19.0"
