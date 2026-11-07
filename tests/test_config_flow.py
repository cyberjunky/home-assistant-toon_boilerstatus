"""Tests for the Toon Boiler Status config and options flows."""

from __future__ import annotations

import aiohttp
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry
from pytest_homeassistant.test_util.aiohttp import AiohttpClientMocker

from custom_components.toon_boilerstatus.const import BASE_URL, DOMAIN

from .conftest import HOST, PORT, mock_toon

USER_INPUT = {CONF_HOST: f" {HOST} ", CONF_PORT: PORT, CONF_NAME: "Boiler", CONF_SCAN_INTERVAL: 30}


async def test_user_flow_success(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """A reachable Toon creates an entry with host/port in data, rest in options."""
    mock_toon(aioclient_mock)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Boiler"
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: PORT}
    assert result["options"] == {CONF_NAME: "Boiler", CONF_SCAN_INTERVAL: 30}
    assert result["result"].unique_id == HOST


async def test_user_flow_cannot_connect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A connection error re-shows the form, and the flow can recover."""
    mock_toon(aioclient_mock, exc=aiohttp.ClientError("boom"))

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_toon(aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_timeout(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """A timeout maps to cannot_connect."""
    mock_toon(aioclient_mock, exc=TimeoutError())

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_invalid_data(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A non-JSON body maps to invalid_data."""
    mock_toon(aioclient_mock, text="<html>not json</html>", headers={"Content-Type": "text/plain"})

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "invalid_data"}


async def test_user_flow_unknown_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """An unexpected exception maps to unknown."""
    mock_toon(aioclient_mock, exc=RuntimeError("boom"))

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["errors"] == {"base": "unknown"}


async def test_user_flow_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """Adding the same host twice aborts."""
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_import_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """YAML import creates an entry when the device is reachable."""
    mock_toon(aioclient_mock)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: HOST, CONF_NAME: "Yaml"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Yaml"
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: PORT}


async def test_import_flow_missing_host(hass: HomeAssistant) -> None:
    """YAML import without host aborts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_NAME: "Yaml"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_import"


async def test_import_flow_cannot_connect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """YAML import aborts when the device is unreachable."""
    mock_toon(aioclient_mock, exc=aiohttp.ClientError("boom"))

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: HOST}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_options_flow_updates_options(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """Changing name/interval updates options and keeps the title in sync."""
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_PORT: PORT, CONF_NAME: "Renamed", CONF_SCAN_INTERVAL: 60},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_NAME: "Renamed", CONF_SCAN_INTERVAL: 60}
    assert mock_config_entry.title == "Renamed"


async def test_options_flow_change_host(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """Changing host validates the new address and updates data and unique_id."""
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    new_host = "192.168.1.60"
    aioclient_mock.get(BASE_URL.format(new_host, PORT), text="{}")

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_HOST: new_host, CONF_PORT: PORT, CONF_NAME: "Toon", CONF_SCAN_INTERVAL: 10},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.data[CONF_HOST] == new_host
    assert mock_config_entry.unique_id == new_host


async def test_options_flow_change_host_cannot_connect(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """An unreachable new host shows an error and leaves the entry untouched."""
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    new_host = "192.168.1.60"
    aioclient_mock.get(BASE_URL.format(new_host, PORT), exc=aiohttp.ClientError("boom"))

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_HOST: new_host, CONF_PORT: PORT, CONF_NAME: "Toon", CONF_SCAN_INTERVAL: 10},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert mock_config_entry.data[CONF_HOST] == HOST


async def test_options_flow_duplicate_host(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, aioclient_mock: AiohttpClientMocker
) -> None:
    """Switching to a host owned by another entry is rejected."""
    other_host = "192.168.1.70"
    MockConfigEntry(domain=DOMAIN, unique_id=other_host, data={CONF_HOST: other_host}).add_to_hass(
        hass
    )
    mock_config_entry.add_to_hass(hass)
    mock_toon(aioclient_mock)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_HOST: other_host, CONF_PORT: PORT, CONF_NAME: "Toon", CONF_SCAN_INTERVAL: 10},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "already_configured"}
