"""
Support for reading Opentherm boiler status data using Toon thermostat's ketelmodule.
Only works for rooted Toon.

configuration.yaml

sensor:
    - platform: toon_boilerstatus
    host: IP_ADDRESS
    port: 80
    scan_interval: 10
    resources:
        - boilersetpoint
        - boilerintemp
        - boilerouttemp
        - boilerpressure
        - boilermodulationlevel
        - roomtemp
        - roomtempsetpoint
"""
import asyncio
import logging
from datetime import timedelta
from typing import Final

import aiohttp
import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_RESOURCES,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

BASE_URL = "http://{0}:{1}/boilerstatus/boilervalues.txt"
_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)
DEFAULT_NAME = "Toon "

SENSOR_LIST = {
    "boilersetpoint",
    "boilerintemp",
    "boilerouttemp",
    "boilerpressure",
    "boilermodulationlevel",
    "roomtemp",
    "roomtempsetpoint",
}

SENSOR_TYPES: Final[tuple[SensorEntityDescription, ...]] = (
    SensorEntityDescription(
        key="boilersetpoint",
        name="Boiler SetPoint",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilerintemp",
        name="Boiler InTemp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilerouttemp",
        name="Boiler OutTemp",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilerpressure",
        name="Boiler Pressure",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="boilermodulationlevel",
        name="Boiler Modulation",
        icon="mdi:fire",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="roomtemp",
        name="Room Temp",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="roomtempsetpoint",
        name="Room Temp SetPoint",
        icon="mdi:thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=80): cv.positive_int,
        vol.Required(CONF_RESOURCES, default=list(SENSOR_LIST)): vol.All(
            cv.ensure_list, [vol.In(SENSOR_LIST)]
        ),
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Toon boilerstatus sensors."""

    session = async_get_clientsession(hass)
    data = ToonBoilerStatusData(session, config.get(CONF_HOST), config.get(CONF_PORT))
    prefix = config.get(CONF_NAME)
    await data.async_update()

    entities = []
    for description in SENSOR_TYPES:
        if description.key in config[CONF_RESOURCES]:
            _LOGGER.debug("Adding Toon Boiler Status sensor: %s", description.name)
            sensor = ToonBoilerStatusSensor(prefix, description, data)
            entities.append(sensor)
    async_add_entities(entities, True)


# pylint: disable=abstract-method
class ToonBoilerStatusData:
    """Handle Toon object and limit updates."""

    def __init__(self, session, host, port):
        """Initialize the data object."""

        self._session = session
        self._url = BASE_URL.format(host, port)
        self.data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Download and update data from Toon."""

        try:
            async with async_timeout.timeout(5):
                response = await self._session.get(
                    self._url, headers={"Accept-Encoding": "identity"}
                )
            self.data = await response.json(content_type="text/plain")
            _LOGGER.debug("Data received from Toon: %s", self.data)
        except aiohttp.ClientError:
            _LOGGER.error("Cannot connect to Toon using url '%s'", self._url)
        except asyncio.TimeoutError:
            _LOGGER.error(
                "Timeout error occurred while connecting to Toon using url '%s'",
                self._url
            )
        except (TypeError, KeyError) as err:
            _LOGGER.error(f"Cannot parse data received from Toon: %s", err)


class ToonBoilerStatusSensor(SensorEntity):
    """Representation of a Toon Boilerstatus sensor."""

    def __init__(self, prefix, description: SensorEntityDescription, data):
        """Initialize the sensor."""
        self.entity_description = description
        self._data = data
        self._prefix = prefix
        self._type = self.entity_description.key
        self._attr_icon = self.entity_description.icon
        self._attr_name = self._prefix + self.entity_description.name
        self._attr_state_class = self.entity_description.state_class
        self._attr_native_unit_of_measurement = (
            self.entity_description.native_unit_of_measurement
        )
        self._attr_device_class = self.entity_description.device_class
        self._attr_unique_id = f"{self._prefix}_{self._type}"

        self._state = None
        self._last_updated = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr["Last Updated"] = self._last_updated
        return attr

    async def async_update(self):
        """Get the latest data and use it to update our sensor state."""

        await self._data.async_update()
        boiler = self._data.data

        if boiler:
            if "sampleTime" in boiler and boiler["sampleTime"] is not None:
                self._last_updated = boiler["sampleTime"]

            if self._type == "boilersetpoint":
                if "boilerSetpoint" in boiler and boiler["boilerSetpoint"] is not None:
                    self._state = float(boiler["boilerSetpoint"])

            elif self._type == "boilerintemp":
                if "boilerInTemp" in boiler and boiler["boilerInTemp"] is not None:
                    self._state = float(boiler["boilerInTemp"])

            elif self._type == "boilerouttemp":
                if "boilerOutTemp" in boiler and boiler["boilerOutTemp"] is not None:
                    self._state = float(boiler["boilerOutTemp"])

            elif self._type == "boilerpressure":
                if "boilerPressure" in boiler and boiler["boilerPressure"] is not None:
                    self._state = float(boiler["boilerPressure"])

            elif self._type == "boilermodulationlevel":
                if (
                    "boilerModulationLevel" in boiler
                    and boiler["boilerModulationLevel"] is not None
                ):
                    self._state = float(boiler["boilerModulationLevel"])

            elif self._type == "roomtemp":
                if "roomTemp" in boiler and boiler["roomTemp"] is not None:
                    self._state = float(boiler["roomTemp"])

            elif self._type == "roomtempsetpoint":
                if (
                    "roomTempSetpoint" in boiler
                    and boiler["roomTempSetpoint"] is not None
                ):
                    self._state = float(boiler["roomTempSetpoint"])

            _LOGGER.debug("Device: %s State: %s", self._type, self._state)
