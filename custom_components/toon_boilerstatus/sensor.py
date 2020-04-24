"""
Support for reading Opentherm boiler status data using TOON thermostat's ketelmodule.
Only works for rooted TOON.

configuration.yaml

sensor:
  - platform: toon_boilerstatus
    host: IP_ADDRESS
    port: 10080
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
    CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_RESOURCES
    )
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

BASE_URL = 'http://{0}:{1}/boilerstatus/boilervalues.txt'
_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

SENSOR_PREFIX = 'TOON '
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
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=10800): cv.positive_int,
    vol.Required(CONF_RESOURCES, default=list(SENSOR_TYPES)):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the TOON boilerstatus sensors."""

    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    toondata = ToonBoilerStatusData(hass, host, port)
    await toondata.async_update()

    entities = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()
        name = SENSOR_PREFIX + SENSOR_TYPES[resource][0]
        unit = SENSOR_TYPES[resource][1]
        icon = SENSOR_TYPES[resource][2]

        _LOGGER.debug("Adding TOON Boiler Status sensor: {}, {}, {}, {}".format(name, sensor_type, unit, icon))
        entities.append(ToonBoilerStatusSensor(toondata, name, sensor_type, unit, icon))

    async_add_entities(entities, True)


# pylint: disable=abstract-method
class ToonBoilerStatusData(object):
    """Handle TOON object and limit updates."""

    def __init__(self, hass, host, port):
        """Initialize the data object."""
        self._hass = hass
        self._host = host
        self._port = port

        self._url = BASE_URL.format(self._host, self._port)
        self._data = None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):

        try:
            websession = async_get_clientsession(self._hass)
            with async_timeout.timeout(10):
                response = await websession.get(self._url)
            _LOGGER.debug(
                "Response status from TOON: %s", response.status
            )
            self._data = await response.json(content_type='text/plain')
            _LOGGER.debug("Data received from TOON: %s", self._data)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Cannot connect to TOON thermostat")
            self._data = None
            return
        except (Exception):
            _LOGGER.error("Error downloading from TOON thermostat")
            self._data = None
            return

    @property
    def latest_data(self):
        """Return the latest data object."""
        return self._data


class ToonBoilerStatusSensor(Entity):
    """Representation of a TOON Boilerstatus sensor."""

    def __init__(self, toondata, name, sensor_type, unit, icon):
        """Initialize the sensor."""
        self._toondata = toondata
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

        await self._toondata.async_update()
        boilerstatus = self._toondata.latest_data

        if boilerstatus:
            if 'sampleTime' in boilerstatus:
              if boilerstatus["sampleTime"] is not None:
                self._last_updated = boilerstatus["sampleTime"]

            if self._type == 'boilersetpoint':
              if 'boilerSetpoint' in boilerstatus:
                if boilerstatus["boilerSetpoint"] is not None:
                  self._state = float(boilerstatus["boilerSetpoint"])

            elif self._type == 'boilerintemp':
              if 'boilerInTemp' in boilerstatus:
                if boilerstatus["boilerInTemp"] is not None:
                  self._state = float(boilerstatus["boilerInTemp"])

            elif self._type == 'boilerouttemp':
              if 'boilerOutTemp' in boilerstatus:
                if boilerstatus["boilerOutTemp"] is not None:
                  self._state = float(boilerstatus["boilerOutTemp"])

            elif self._type == 'boilerpressure':
              if 'boilerPressure' in boilerstatus:
                if boilerstatus["boilerPressure"] is not None:
                  self._state = float(boilerstatus["boilerPressure"])

            elif self._type == 'boilermodulationlevel':
              if 'boilerModulationLevel' in boilerstatus:
                if boilerstatus["boilerModulationLevel"] is not None:
                  self._state = float(boilerstatus["boilerModulationLevel"])

            elif self._type == 'roomtemp':
              if 'roomTemp' in boilerstatus:
                if boilerstatus["roomTemp"] is not None:
                  self._state = float(boilerstatus["roomTemp"])

            elif self._type == 'roomtempsetpoint':
              if 'roomTempSetpoint' in boilerstatus:
                if boilerstatus["roomTempSetpoint"] is not None:
                  self._state = float(boilerstatus["roomTempSetpoint"])

            _LOGGER.debug("Device: {} State: {}".format(self._type, self._state))
