"""Constants for the Omnik Inverter integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)

DOMAIN: Final = "omnik_inverter"

# Configuration keys
CONF_SERIAL_NUMBER: Final = "serial_number"

# Defaults
DEFAULT_NAME: Final = "Omnik"
DEFAULT_PORT: Final = 8899
DEFAULT_SCAN_INTERVAL: Final = 60
DEFAULT_TIMEOUT: Final = 10

# Platforms
PLATFORMS: Final = ["sensor"]
