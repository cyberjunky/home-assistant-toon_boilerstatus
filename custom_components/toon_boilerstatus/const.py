"""Constants for the Toon Boiler Status integration."""

from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, Platform, UnitOfPressure, UnitOfTemperature

DOMAIN: Final = "toon_boilerstatus"

# Platforms
PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]

# Configuration constants
CONF_RESOURCES = "resources"

# Default values
DEFAULT_NAME = "Toon"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 10

# API
BASE_URL = "http://{0}:{1}/boilerstatus/boilervalues.txt"

# Sensor keys
SENSOR_BOILER_SETPOINT = "boilersetpoint"
SENSOR_BOILER_INTEMP = "boilerintemp"
SENSOR_BOILER_OUTTEMP = "boilerouttemp"
SENSOR_BOILER_PRESSURE = "boilerpressure"
SENSOR_BOILER_MODULATION = "boilermodulationlevel"
SENSOR_ROOM_TEMP = "roomtemp"
SENSOR_ROOM_TEMP_SETPOINT = "roomtempsetpoint"

# All available sensors
SENSOR_TYPES: Final[tuple[SensorEntityDescription, ...]] = (
    SensorEntityDescription(
        key=SENSOR_BOILER_SETPOINT,
        name="Boiler SetPoint",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_BOILER_INTEMP,
        name="Boiler InTemp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_BOILER_OUTTEMP,
        name="Boiler OutTemp",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_BOILER_PRESSURE,
        name="Boiler Pressure",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_BOILER_MODULATION,
        name="Boiler Modulation",
        icon="mdi:fire",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_ROOM_TEMP,
        name="Room Temp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_ROOM_TEMP_SETPOINT,
        name="Room Temp SetPoint",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Map sensor keys for quick lookup
SENSOR_MAP = {desc.key: desc for desc in SENSOR_TYPES}
SENSOR_KEYS = [desc.key for desc in SENSOR_TYPES]
