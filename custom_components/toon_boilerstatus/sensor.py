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
import logging
from datetime import timedelta
import aiohttp
import asyncio
import async_timeout
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_RESOURCES
    )
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

BASE_URL = 'http://{0}:{1}/boilerstatus/boilervalues.txt'
_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)
DEFAULT_NAME = 'Toon '

SENSOR_TYPES = {
    'boilersetpoint': ['Boiler SetPoint', '°C', 'mdi:thermometer'],
    'boilerintemp': ['Boiler InTemp', '°C', 'mdi:thermometer'],
    'boilerouttemp': ['Boiler OutTemp', '°C', 'mdi:thermometer'],
    'boilerpressure': ['Boiler Pressure', 'Bar', 'mdi:gauge'],
    'boilermodulationlevel': ['Boiler Modulation', '%', 'mdi:fire'],
    'roomtemp': ['Room Temp', '°C', 'mdi:thermometer'],
    'roomtempsetpoint': ['Room Temp SetPoint', '°C', 'mdi:thermometer'],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=80): cv.positive_int,
    vol.Required(CONF_RESOURCES, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Toon boilerstatus sensors."""

    session = async_get_clientsession(hass)
    data = ToonBoilerStatusData(session, config.get(CONF_HOST), config.get(CONF_PORT))
    prefix = config.get(CONF_NAME)
    await data.async_update()
    
    entities = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()
        name = prefix + " " + SENSOR_TYPES[resource][0]
        unit = SENSOR_TYPES[resource][1]
        icon = SENSOR_TYPES[resource][2]

        _LOGGER.debug("Adding Toon Boiler Status sensor: {}, {}, {}, {}".format(name, sensor_type, unit, icon))
        entities.append(ToonBoilerStatusSensor(data, name, sensor_type, unit, icon))

    async_add_entities(entities, True)


# pylint: disable=abstract-method
class ToonBoilerStatusData(object):
    """Handle Toon object and limit updates."""
    def __init__(self, session, host, port):
        """Initialize the data object."""

        self._session = session
        self._url = BASE_URL.format(host, port)
        self._data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Download and update data from Toon."""

        try:
            with async_timeout.timeout(5):
                response = await self._session.get(self._url, headers={"Accept-Encoding": "identity"})
        except aiohttp.ClientError:
            _LOGGER.error("Cannot poll Toon using url: %s", self._url)
            return
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout error occurred while polling Toon using url: %s", self._url)
            return
        except Exception as err:
            _LOGGER.error("Unknown error occurred while polling Toon: %s", err)
            self._data = None
            return

        try:
            self._data = await response.json(content_type='text/plain')
            _LOGGER.debug("Data received from Toon: %s", self._data)
        except Exception as err:
            _LOGGER.error("Cannot parse data received from Toon: %s", err)
            self._data = None
            return

    @property
    def latest_data(self):
        """Return the latest data object."""
        return self._data


class ToonBoilerStatusSensor(Entity):
    """Representation of a Toon Boilerstatus sensor."""

    def __init__(self, data, name, sensor_type, unit, icon):
        """Initialize the sensor."""
        self._data = data
        self._name = name
        self._type = sensor_type
        self._unit = unit
        self._icon = icon

        self._state = None
        self._last_updated = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_state_attributes(self):
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr['Last Updated'] = self._last_updated
        return attr

    async def async_update(self):
        """Get the latest data and use it to update our sensor state."""

        await self._data.async_update()
        boiler = self._data.latest_data

        if boiler:
            if 'sampleTime' in boiler:
              if boiler["sampleTime"] is not None:
                self._last_updated = boiler["sampleTime"]

            if self._type == 'boilersetpoint':
              if 'boilerSetpoint' in boiler:
                if boiler["boilerSetpoint"] is not None:
                  self._state = float(boiler["boilerSetpoint"])

            elif self._type == 'boilerintemp':
              if 'boilerInTemp' in boiler:
                if boiler["boilerInTemp"] is not None:
                  self._state = float(boiler["boilerInTemp"])

            elif self._type == 'boilerouttemp':
              if 'boilerOutTemp' in boiler:
                if boiler["boilerOutTemp"] is not None:
                  self._state = float(boiler["boilerOutTemp"])

            elif self._type == 'boilerpressure':
              if 'boilerPressure' in boiler:
                if boiler["boilerPressure"] is not None:
                  self._state = float(boiler["boilerPressure"])

            elif self._type == 'boilermodulationlevel':
              if 'boilerModulationLevel' in boiler:
                if boiler["boilerModulationLevel"] is not None:
                  self._state = float(boiler["boilerModulationLevel"])

            elif self._type == 'roomtemp':
              if 'roomTemp' in boiler:
                if boiler["roomTemp"] is not None:
                  self._state = float(boiler["roomTemp"])

            elif self._type == 'roomtempsetpoint':
              if 'roomTempSetpoint' in boiler:
                if boiler["roomTempSetpoint"] is not None:
                  self._state = float(boiler["roomTempSetpoint"])

            _LOGGER.debug("Device: {} State: {}".format(self._type, self._state))
