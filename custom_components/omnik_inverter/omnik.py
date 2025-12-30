"""Omnik Inverter TCP communication module.

This module handles async TCP communication with Omnik solar inverters.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)

# Minimum expected message length for valid response
MIN_MESSAGE_LENGTH = 80


class OmnikConnectionError(Exception):
    """Exception raised when connection to inverter fails."""


class OmnikParseError(Exception):
    """Exception raised when parsing inverter data fails."""


@dataclass
class OmnikInverterData:
    """Dataclass representing parsed inverter data."""

    serial_number: str | None
    status: str  # "Online" / "Offline"
    temperature: float | None
    actual_power: int
    energy_today: float | None
    energy_total: float | None
    hours_total: int | None
    dc_input_voltage: float | None
    dc_input_current: float | None
    ac_output_voltage: float | None
    ac_output_current: float | None
    ac_output_frequency: float | None
    ac_output_power: int | None


class OmnikInverter:
    """Class for async communication with Omnik inverters."""

    def __init__(
        self,
        host: str,
        port: int,
        serial_number: int,
        timeout: int = 10,
    ) -> None:
        """Initialize the Omnik inverter connection.

        Args:
            host: IP address of the inverter
            port: TCP port of the inverter
            serial_number: Serial number of the inverter
            timeout: Connection timeout in seconds
        """
        self._host = host
        self._port = port
        self._serial_number = serial_number
        self._timeout = timeout
        self._raw_msg: bytes | None = None

    @staticmethod
    def _generate_request(serial_number: int) -> bytes:
        """Generate the request message for the inverter.

        The request is built from:
        - Fixed 4-byte header
        - Reversed hex notation of serial number (doubled)
        - Fixed 2-byte separator
        - Checksum byte
        - Fixed ending byte

        Args:
            serial_number: Serial number of the inverter

        Returns:
            Bytes containing the request message
        """
        # Convert serial number to bytes (doubled and reversed)
        double_hex = hex(serial_number)[2:] * 2
        serial_bytes = bytearray.fromhex(double_hex)
        serial_bytes.reverse()

        # Calculate checksum
        cs_count = 115 + sum(serial_bytes)
        checksum = cs_count & 0xFF  # Take last byte

        # Build request message
        request_data = bytearray([0x68, 0x02, 0x40, 0x30])
        request_data.extend(serial_bytes)
        request_data.extend([0x01, 0x00])
        request_data.append(checksum)
        request_data.append(0x16)

        return bytes(request_data)

    async def _async_fetch_data(self) -> bytes:
        """Fetch raw data from the inverter.

        Returns:
            Raw bytes received from the inverter

        Raises:
            OmnikConnectionError: If connection fails
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError as err:
            raise OmnikConnectionError(
                f"Connection to {self._host}:{self._port} timed out"
            ) from err
        except OSError as err:
            raise OmnikConnectionError(
                f"Could not connect to inverter at {self._host}:{self._port}: {err}"
            ) from err

        try:
            # Send request
            request = self._generate_request(self._serial_number)
            writer.write(request)
            await writer.drain()

            # Read response with timeout
            data = await asyncio.wait_for(
                reader.read(1024),
                timeout=self._timeout,
            )

            if not data:
                raise OmnikConnectionError("No data received from inverter")

            _LOGGER.debug(
                "Received %d bytes from inverter at %s:%s",
                len(data),
                self._host,
                self._port,
            )

            return data

        except asyncio.TimeoutError as err:
            raise OmnikConnectionError(
                f"Timeout waiting for response from {self._host}:{self._port}"
            ) from err
        finally:
            writer.close()
            await writer.wait_closed()

    def _get_string(self, begin: int, end: int) -> str | None:
        """Extract string from message.

        Args:
            begin: Starting byte index
            end: End byte index

        Returns:
            Decoded string or None if extraction fails
        """
        if self._raw_msg is None:
            return None

        try:
            return self._raw_msg[begin:end].decode().strip("\x00")
        except (UnicodeDecodeError, IndexError):
            return None

    def _get_short(self, begin: int, divider: int = 10) -> float | None:
        """Extract short (2 bytes) from message.

        Args:
            begin: Index of short in message
            divider: Divider to convert to float

        Returns:
            Extracted value or None if extraction fails
        """
        if self._raw_msg is None or len(self._raw_msg) < begin + 2:
            return None

        try:
            num = struct.unpack("!H", self._raw_msg[begin : begin + 2])[0]
            if num == 65535:
                return None  # Invalid value
            return float(num) / divider
        except struct.error:
            return None

    def _get_long(self, begin: int, divider: int = 10) -> float | None:
        """Extract long (4 bytes) from message.

        Args:
            begin: Index of long in message
            divider: Divider to convert to float

        Returns:
            Extracted value or None if extraction fails
        """
        if self._raw_msg is None or len(self._raw_msg) < begin + 4:
            return None

        try:
            value = struct.unpack("!I", self._raw_msg[begin : begin + 4])[0]
            return float(value) / divider
        except struct.error:
            return None

    def _parse_data(self) -> OmnikInverterData:
        """Parse the raw message into structured data.

        Returns:
            OmnikInverterData with parsed values
        """
        # Check if we have valid data
        if self._raw_msg is None or len(self._raw_msg) < MIN_MESSAGE_LENGTH:
            _LOGGER.debug(
                "Invalid or no data from inverter (length: %s)",
                len(self._raw_msg) if self._raw_msg else 0,
            )
            return OmnikInverterData(
                serial_number=None,
                status="Offline",
                temperature=None,
                actual_power=0,
                energy_today=None,
                energy_total=None,
                hours_total=None,
                dc_input_voltage=None,
                dc_input_current=None,
                ac_output_voltage=None,
                ac_output_current=None,
                ac_output_frequency=None,
                ac_output_power=None,
            )

        # Check if inverter is operational (temperature is valid indicator)
        temperature = self._get_short(31)
        if temperature is not None and temperature > 150:
            temperature = None

        is_online = temperature is not None

        # Parse actual power
        actual_power_raw = self._get_short(59, 1)
        actual_power = int(actual_power_raw) if actual_power_raw is not None else 0

        # Parse hours total
        hours_total_raw = self._get_long(75, 1)
        hours_total = int(hours_total_raw) if hours_total_raw is not None else None

        # Parse AC output power
        ac_power_raw = self._get_short(59, 1)
        ac_output_power = int(ac_power_raw) if ac_power_raw is not None else None

        return OmnikInverterData(
            serial_number=self._get_string(15, 31),
            status="Online" if is_online else "Offline",
            temperature=temperature,
            actual_power=actual_power if is_online else 0,
            energy_today=self._get_short(69, 100),
            energy_total=self._get_long(71),
            hours_total=hours_total,
            dc_input_voltage=self._get_short(33),
            dc_input_current=self._get_short(39),
            ac_output_voltage=self._get_short(51),
            ac_output_current=self._get_short(45),
            ac_output_frequency=self._get_short(57, 100),
            ac_output_power=ac_output_power,
        )

    async def async_get_data(self) -> OmnikInverterData:
        """Get data from the inverter.

        Returns:
            OmnikInverterData with current inverter values

        Raises:
            OmnikConnectionError: If connection fails
        """
        try:
            self._raw_msg = await self._async_fetch_data()
            return self._parse_data()
        except OmnikConnectionError:
            # Re-raise connection errors
            raise
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching inverter data")
            raise OmnikConnectionError(
                f"Unexpected error: {err}"
            ) from err

    async def async_test_connection(self) -> bool:
        """Test connection to the inverter.

        Returns:
            True if connection successful

        Raises:
            OmnikConnectionError: If connection fails
        """
        await self._async_fetch_data()
        return True
