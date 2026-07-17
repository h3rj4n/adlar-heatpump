"""Number platform for Adlar Heatpump (writable setpoints)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUMBER_DESCRIPTIONS, AdlarNumberDescription
from .coordinator import AdlarCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AdlarCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AdlarNumber(coordinator, description) for description in NUMBER_DESCRIPTIONS
    )


class AdlarNumber(CoordinatorEntity[AdlarCoordinator], NumberEntity):
    """Writable setpoint/parameter entity backed by an AdlarNumberDescription."""

    entity_description: AdlarNumberDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: AdlarCoordinator, description: AdlarNumberDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry_id}_num_{description.address:04X}"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self.entity_description.address)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(self.entity_description.address, int(value))

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.entry_id)},
            "name": "Adlar Aurora II Heatpump",
            "manufacturer": "Adlar",
            "model": "Aurora II",
        }
