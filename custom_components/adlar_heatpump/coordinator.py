"""Modbus TCP data coordinator for Adlar Heatpump."""
from __future__ import annotations

import logging
import ctypes
import time
from datetime import timedelta
from typing import Any, NamedTuple
from pymodbus.client import ModbusTcpClient

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SENSOR_REGISTERS,
    STATUS_REGISTER,
    NUMBER_DESCRIPTIONS,
    SWITCH_REGISTER,
    SELECT_REGISTERS,
    ENERGY_REGISTER,
    REFRIGERANT_REGISTER,
    REFRIGERANT_TYPES,
    get_temperature_scale,
)

_LOGGER = logging.getLogger(__name__)

# Delay between every Modbus request (reads and writes).
# The EW11 WiFi-to-RS485 bridge and JPX-3002 splitter need a small inter-
# request gap to avoid dropped frames. With block reads we make ~8 requests
# per poll instead of ~35, so even 50 ms here costs only ~400 ms total vs
# the previous 7 s. Raise if you see repeated read errors in the log;
# lower (or set to 0) if your hardware handles back-to-back requests fine.
INTER_REQUEST_DELAY = 0.05  # seconds between every read request
WRITE_DELAY = 0.2           # seconds before each write (kept conservative)

TEMPERATURE_DEVICE_CLASS = "temperature"

class _Block(NamedTuple):
    """Start/end address pair (both inclusive) for a bulk register read."""
    start: int
    end: int


# Consecutive (or near-consecutive) registers grouped into single
# read_holding_registers calls. Gaps within a block are fetched but discarded.
#
# Isolated single reads: 0x0027 (compressor target), 0x0000 (status),
#                        0x0085 (DC bus), 0x011A (hysteresis), 0x01A3 (min flow).
_REGISTER_BLOCKS: dict[str, _Block] = {
    "sensors":  _Block(0x0040, 0x005D),  # 30 regs — SENSOR_REGISTERS + ENERGY_REGISTER
    "config12": _Block(0x0158, 0x0164),  # 13 regs — silent-mode freqs + pump-speed params (9-reg gap)
    "config3":  _Block(0x0204, 0x0205),  #  2 regs — max / constant pump speed
    "ctrl":     _Block(0x0300, 0x0316),  # 23 regs — setpoints, mode, ON/OFF, curves (11-reg gap)
}


# ── Pure helpers ───────────────────────────────────────────────────────────────

def _to_signed(value: int) -> int:
    return ctypes.c_int16(value).value


def _apply_scale(
    raw: int | None,
    device_class: str | None,
    scale: float,
    signed: bool,
    temperature_scale: float,
) -> int | float | None:
    """Convert raw register value to a scaled sensor value."""
    if raw is None:
        return None
    value = _to_signed(raw) if signed else raw
    effective_scale = temperature_scale if device_class == TEMPERATURE_DEVICE_CLASS else scale
    return round(value * effective_scale, 1) if effective_scale != 1 else value


class AdlarCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, host, port, slave, scan_interval):
        self.host = host
        self.port = port
        self.slave = slave
        self._client: ModbusTcpClient | None = None
        self.refrigerant_type: int | None = None
        self.refrigerant_name: str = "Unknown"
        self.temperature_scale: float = 1.0  # default R32
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def entry_id(self) -> str:
        """Return the config entry ID.

        `DataUpdateCoordinator.config_entry` is typed `ConfigEntry | None`
        because the base class supports being constructed outside a config
        entry context. In this integration it is always created from
        `async_setup_entry`, so it is always set in practice; the assert
        narrows the type for callers instead of every platform reaching into
        `coordinator.config_entry.entry_id` (and re-triggering the same
        possibly-None warning) themselves.
        """
        assert self.config_entry is not None
        return self.config_entry.entry_id

    def _get_client(self) -> ModbusTcpClient:
        """Return connected client, reconnect if needed."""
        if self._client is None or not self._client.connected:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass
            self._client = ModbusTcpClient(host=self.host, port=self.port, timeout=10)
            self._client.connect()
        return self._client

    def _read_one(self, address: int) -> int | None:
        """Read a single holding register. Reconnects on failure.

        No address offset is applied. pymodbus uses 0-based addressing natively,
        identical to jsmodbus. Register 0x0040 = address 0x0040.
        """
        time.sleep(INTER_REQUEST_DELAY)
        try:
            client = self._get_client()
            result = client.read_holding_registers(
                address=address, count=1, device_id=self.slave
            )
            if hasattr(result, "isError") and result.isError():
                _LOGGER.warning("Error reading register 0x%04X", address)
                return None
            return result.registers[0]
        except Exception as err:
            _LOGGER.warning("Exception reading 0x%04X: %s — reconnecting", address, err)
            self._client = None
            return None

    def _read_block(self, start: int, count: int) -> list[int | None]:
        """Read `count` consecutive holding registers starting at `start`.

        Returns a list of raw values (int). On failure the entire block is
        returned as None values so callers can continue with partial data.
        """
        time.sleep(INTER_REQUEST_DELAY)
        try:
            client = self._get_client()
            result = client.read_holding_registers(
                address=start, count=count, device_id=self.slave
            )
            if hasattr(result, "isError") and result.isError():
                _LOGGER.warning("Error reading block 0x%04X[%d]", start, count)
                return [None] * count
            return list(result.registers)
        except Exception as err:
            _LOGGER.warning(
                "Exception reading block 0x%04X[%d]: %s — reconnecting", start, count, err
            )
            self._client = None
            return [None] * count

    def _detect_refrigerant(self) -> None:
        """Read P119 (0x0177) and set temperature scaling.

        Called once on the first poll.
        R32  (2) → ×1.0  (direct °C values)
        R290 (3) → ×0.1  (raw/10 = °C)
        R410A(1) → ×1.0  (assumed same as R32)
        """
        raw = self._read_one(REFRIGERANT_REGISTER)
        if raw is None:
            _LOGGER.warning(
                "P119 (0x0177) unreadable — default temperature scaling ×1 (R32)"
            )
            return

        self.refrigerant_type = raw
        self.refrigerant_name = REFRIGERANT_TYPES.get(raw, f"Unknown ({raw})")
        self.temperature_scale = get_temperature_scale(raw)

        _LOGGER.info(
            "Refrigerant detected: %s (P119=%d) — temperature scaling: ×%s",
            self.refrigerant_name,
            raw,
            self.temperature_scale,
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch_all)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with heatpump: {err}") from err

    def _fetch_all(self) -> dict:
        data: dict = {}

        # ── One-time: refrigerant detection ──
        # Results live on coordinator.refrigerant_name / coordinator.temperature_scale;
        # they are not polled register values and are not stored in data.
        if self.refrigerant_type is None:
            self._detect_refrigerant()

        # ── Build flat address → raw-value map ─────────────────────────────
        # Each block read covers a contiguous range; addresses not in any block
        # (currently 0x0085, 0x011A, 0x01A3) are single-read on demand below.
        raw: dict[int, int | None] = {}
        for b in _REGISTER_BLOCKS.values():
            block = self._read_block(b.start, b.end - b.start + 1)
            for offset, value in enumerate(block):
                raw[b.start + offset] = value

        raw[STATUS_REGISTER] = self._read_one(STATUS_REGISTER)  # 0x0000
        raw[0x0027]           = self._read_one(0x0027)           # compressor target freq

        # ── Populate data from raw ─────────────────────────────────────────

        # Compressor target frequency
        data[0x0027] = raw[0x0027]

        # Status bitmask — binary_sensor entities apply their own mask
        data[STATUS_REGISTER] = raw[STATUS_REGISTER]

        # Sensor registers — fall back to single read for addresses outside all blocks
        for address, name, unit, device_class, scale, signed in SENSOR_REGISTERS:
            if address not in raw:
                raw[address] = self._read_one(address)
            data[address] = _apply_scale(raw[address], device_class, scale, signed, self.temperature_scale)

        # Energy register (0x005D — covered by sensors block)
        r = raw.get(ENERGY_REGISTER)
        data[ENERGY_REGISTER] = float(r) if r is not None else None

        # Number descriptions — 0x011A and 0x01A3 are not in any block
        for desc in NUMBER_DESCRIPTIONS:
            if desc.address not in raw:
                raw[desc.address] = self._read_one(desc.address)
            r = raw[desc.address]
            data[desc.address] = _to_signed(r) if r is not None else None

        # Switch (0x0305 — covered by ctrl block)
        r = raw.get(SWITCH_REGISTER)
        data[SWITCH_REGISTER] = bool(r) if r is not None else None

        # Select registers (all covered by ctrl block)
        for address, name, options_map in SELECT_REGISTERS:
            if address not in raw:
                raw[address] = self._read_one(address)
            r = raw[address]
            if r is None:
                data[address] = None
            else:
                rev = {v: k for k, v in options_map.items()}
                data[address] = rev.get(r, f"Unknown ({r})")

        return data

    def write_register(self, address: int, value: int) -> bool:
        """Write a single holding register."""
        try:
            time.sleep(WRITE_DELAY)
            client = self._get_client()
            result = client.write_register(
                address=address, value=value, device_id=self.slave
            )
            return not result.isError()
        except Exception as err:
            _LOGGER.error("Write error at 0x%04X: %s", address, err)
            self._client = None
            return False

    def _decode_single(self, address: int, raw: int) -> Any:
        """Apply the same decoding _fetch_all uses for a single raw register value."""
        if address == SWITCH_REGISTER:
            return bool(raw)
        for desc in NUMBER_DESCRIPTIONS:
            if desc.address == address:
                return _to_signed(raw)
        for reg_address, _name, options_map in SELECT_REGISTERS:
            if reg_address == address:
                rev = {v: k for k, v in options_map.items()}
                return rev.get(raw, f"Unknown ({raw})")
        return raw

    def _write_and_read(self, address: int, value: int) -> int | None:
        """Blocking: write register then immediately read it back.

        Returns the new raw register value, or None if either operation failed.
        """
        if not self.write_register(address, value):
            return None
        return self._read_one(address)

    async def async_write_register(self, address: int, value: int) -> bool:
        """Write a register and update coordinator data without a full poll.

        Writes the value, reads back the confirmed register, decodes it, stores
        it in coordinator.data, and notifies all subscribed entities immediately.
        Returns True on success.
        """
        raw = await self.hass.async_add_executor_job(
            self._write_and_read, address, value
        )
        if raw is None or self.data is None:
            return False
        self.data[address] = self._decode_single(address, raw)
        self.async_update_listeners()
        return True
