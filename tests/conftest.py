"""Fixtures for Toon Boiler Status tests."""

from __future__ import annotations

import json
from typing import Any

import pytest
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.toon_boilerstatus.const import BASE_URL, DOMAIN

HOST = "192.168.1.50"
PORT = 80
URL = BASE_URL.format(HOST, PORT)

MOCK_DATA: dict[str, Any] = {
    "sampleTime": "07-11-2026 12:00:00",
    "boilerSetpoint": 55.0,
    "boilerInTemp": 40.5,
    "boilerOutTemp": 52.25,
    "boilerPressure": 1.6,
    "boilerModulationLevel": 30,
    "roomTemp": 20.5,
    "roomTempSetpoint": 21.0,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom_components in every test."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry for a Toon device."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Toon",
        unique_id=HOST,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        options={CONF_NAME: "Toon", CONF_SCAN_INTERVAL: 10},
        entry_id="test_entry_id",
    )


def mock_toon(aioclient_mock: AiohttpClientMocker, data: Any = None, **kwargs: Any) -> None:
    """Register the Toon boilervalues endpoint on the aiohttp mocker."""
    aioclient_mock.clear_requests()
    if kwargs:
        aioclient_mock.get(URL, **kwargs)
        return
    aioclient_mock.get(
        URL,
        text=json.dumps(MOCK_DATA if data is None else data),
        headers={"Content-Type": "text/plain"},
    )
