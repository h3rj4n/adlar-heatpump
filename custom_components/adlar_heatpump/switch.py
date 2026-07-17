"""Switch platform for Adlar Heatpump (ON/OFF)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCH_REGISTER
from .coordinator import AdlarCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AdlarCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AdlarSwitch(coordinator)])


class AdlarSwitch(CoordinatorEntity[AdlarCoordinator], SwitchEntity):
    def __init__(self, coordinator: AdlarCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry_id}_onoff"
        self._attr_name = "Heatpump ON/OFF"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(SWITCH_REGISTER)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_register(SWITCH_REGISTER, 1)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_register(SWITCH_REGISTER, 0)

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }
