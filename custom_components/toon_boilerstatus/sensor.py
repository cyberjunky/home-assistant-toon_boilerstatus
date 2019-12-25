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
import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
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

    scan_interval = config.get(CONF_SCAN_INTERVAL)
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    data = ToonBoilerStatusData(host, port)
    try:
        await data.async_update()
    except ValueError as err:
        _LOGGER.error("Error while fetching data from TOON: %s", err)
        return

    entities = []
    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()
        name = SENSOR_PREFIX + SENSOR_TYPES[resource][0]
        unit = SENSOR_TYPES[resource][1]
        icon = SENSOR_TYPES[resource][2]

        _LOGGER.debug("Adding TOON Boiler Status sensor: {}, {}, {}, {}".format(sensor_type, name, unit, icon))
        entities.append(ToonBoilerStatusSensor(data, sensor_type, name, unit, icon))

    async_add_entities(entities, True)


# pylint: disable=abstract-method
class ToonBoilerStatusData(object):
    """Handle TOON object and limit updates."""

    def __init__(self, host, port):
        """Initialize the data object."""
        self._host = host
        self._port = port
        self._data = None

    def _build_url(self):
        """Build the URL for the requests."""
        url = BASE_URL.format(self._host, self._port)
        _LOGGER.debug("TOON fetch URL: %s", url)
        return url

    @property
    def latest_data(self):
        """Return the latest data object."""
        if self._data:
            return self._data
        return None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Update the data from TOON."""
        try:
            self._data = requests.get(self._build_url(), timeout=10, headers={'accept-encoding': None}).json()
            _LOGGER.debug("TOON fetched data = %s", self._data)
        except (requests.exceptions.RequestException) as error:
            _LOGGER.error("Unable to connect to TOON: %s", error)
            self._data = None

class ToonBoilerStatusSensor(Entity):
    """Representation of a OpenTherm Boiler connected to TOON."""

    def __init__(self, data, sensor_type, name, unit, icon):
        """Initialize the sensor."""
        self._data = data
        self._type = sensor_type
        self._name = name
        self._unit = unit
        self._icon = icon

        self._state = None

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
        if not self._data:
            _LOGGER.error("Didn't receive data from TOON")
            return

        boilerstatus = self._data.latest_data

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
