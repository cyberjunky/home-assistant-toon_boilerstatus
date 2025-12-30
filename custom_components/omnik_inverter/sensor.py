"""Sensor platform for Omnik Inverter integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SERIAL_NUMBER, DEFAULT_NAME, DOMAIN
from .coordinator import OmnikDataUpdateCoordinator
from .omnik import OmnikInverterData

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class OmnikSensorEntityDescription(SensorEntityDescription):
    """Describes an Omnik sensor entity."""

    value_fn: Callable[[OmnikInverterData], str | int | float | None]


SENSOR_DESCRIPTIONS: tuple[OmnikSensorEntityDescription, ...] = (
    OmnikSensorEntityDescription(
        key="status",
        translation_key="status",
        name="Status",
        icon="mdi:solar-power",
        value_fn=lambda data: data.status,
    ),
    OmnikSensorEntityDescription(
        key="actual_power",
        translation_key="actual_power",
        name="Actual Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny",
        value_fn=lambda data: data.actual_power,
    ),
    OmnikSensorEntityDescription(
        key="energy_today",
        translation_key="energy_today",
        name="Energy Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.energy_today,
    ),
    OmnikSensorEntityDescription(
        key="energy_total",
        translation_key="energy_total",
        name="Energy Total",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.energy_total,
    ),
    OmnikSensorEntityDescription(
        key="hours_total",
        translation_key="hours_total",
        name="Hours Total",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer",
        value_fn=lambda data: data.hours_total,
    ),
    OmnikSensorEntityDescription(
        key="inverter_serial_number",
        translation_key="inverter_serial_number",
        name="Inverter Serial Number",
        icon="mdi:information-outline",
        value_fn=lambda data: data.serial_number,
    ),
    OmnikSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        value_fn=lambda data: data.temperature,
    ),
    OmnikSensorEntityDescription(
        key="dc_input_voltage",
        translation_key="dc_input_voltage",
        name="DC Input Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.dc_input_voltage,
    ),
    OmnikSensorEntityDescription(
        key="dc_input_current",
        translation_key="dc_input_current",
        name="DC Input Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.dc_input_current,
    ),
    OmnikSensorEntityDescription(
        key="ac_output_voltage",
        translation_key="ac_output_voltage",
        name="AC Output Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.ac_output_voltage,
    ),
    OmnikSensorEntityDescription(
        key="ac_output_current",
        translation_key="ac_output_current",
        name="AC Output Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.ac_output_current,
    ),
    OmnikSensorEntityDescription(
        key="ac_output_frequency",
        translation_key="ac_output_frequency",
        name="AC Output Frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sine-wave",
        value_fn=lambda data: data.ac_output_frequency,
    ),
    OmnikSensorEntityDescription(
        key="ac_output_power",
        translation_key="ac_output_power",
        name="AC Output Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-outline",
        value_fn=lambda data: data.ac_output_power,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Omnik Inverter sensors from a config entry."""
    coordinator: OmnikDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        OmnikSensorEntity(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class OmnikSensorEntity(CoordinatorEntity[OmnikDataUpdateCoordinator], SensorEntity):
    """Representation of an Omnik Inverter sensor."""

    entity_description: OmnikSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OmnikDataUpdateCoordinator,
        entry: ConfigEntry,
        description: OmnikSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        # Get device name from config entry title
        device_name = entry.title or DEFAULT_NAME
        serial_number = entry.data[CONF_SERIAL_NUMBER]

        # Set unique ID
        self._attr_unique_id = f"{serial_number}_{description.key}"

        # Set device info for grouping
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(serial_number))},
            name=device_name,
            manufacturer="Omnik",
            model="Solar Inverter",
            serial_number=str(serial_number),
        )

    @property
    def native_value(self) -> str | int | float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
