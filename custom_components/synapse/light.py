from __future__ import annotations

import logging
from typing import Any, List, Optional

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .synapse.base_entity import SynapseBaseEntity
from .synapse.bridge import SynapseBridge
from .synapse.const import DOMAIN, SynapseLightDefinition

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform.

    Creates light entities from app configuration and sets up dynamic
    entity registration for runtime configuration updates.
    """
    bridge: SynapseBridge = hass.data[DOMAIN][config_entry.entry_id]

    # Use dynamic configuration if available, otherwise fall back to static config
    entities: List[SynapseLightDefinition] = []
    if bridge._current_configuration and "light" in bridge._current_configuration:
        entities = bridge._current_configuration.get("light", [])
    else:
        entities = bridge.app_data.get("light", [])

    if entities:
        async_add_entities(SynapseLight(hass, bridge, entity) for entity in entities)

    # Listen for registration events to add new entities dynamically
    async def handle_registration(event):
        """Handle registration events to add new light entities.

        Called when an app sends updated configuration. Adds new light 
        entities that weren't present in the initial configuration.
        """
        if event.data.get("unique_id") == bridge.metadata_unique_id:
            # Check if there are new light entities in the dynamic configuration
            if bridge._current_configuration and "light" in bridge._current_configuration:
                new_entities = bridge._current_configuration.get("light", [])
                if new_entities:
                    async_add_entities(SynapseLight(hass, bridge, entity) for entity in new_entities)

    # Register the event listener
    hass.bus.async_listen(bridge.event_name("register"), handle_registration)

class SynapseLight(SynapseBaseEntity, LightEntity):
    """Home Assistant light entity for Synapse apps.

    Represents a numeric input from a connected NodeJS app. Handles
    numeric value updates and user interactions through the bridge.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        bridge: SynapseBridge,
        entity: SynapseLightDefinition,
    ) -> None:
        """Initialize the light entity."""
        super().__init__(hass, bridge, entity)
        self.logger: logging.Logger = logging.getLogger(__name__)

    @property
    def is_on(self) -> bool:
        return self.entity.get("is_on", False)

    @property
    def brightness(self) -> Optional[float]:
        return self.entity.get("brightness")

    @property
    def color_temp_kelvin(self) -> Optional[float]:
        return self.entity.get("color_temp_kelvin")

    @property
    def supported_features(self) -> int:
        return self.entity.get("supported_features", 0)

    @property
    def supported_color_modes(self):
        return self.entity.get("supported_color_modes")

    @property
    def color_mode(self):
        return self.entity.get("color_mode")

    @callback
    async def async_turn_on(self, **kwargs) -> None:
        """Handle turn_on."""
        await self.bridge.emit_event(
            "turn_on",
            {"unique_id": self.entity.get("unique_id"), **kwargs},
        )
    
    @callback
    async def async_turn_off(self, **kwargs) -> None:
        """Handle turn_off."""
        await self.bridge.emit_event(
            "turn_off",
            {"unique_id": self.entity.get("unique_id"), **kwargs},
        )
