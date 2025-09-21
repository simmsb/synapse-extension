import logging

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
    """Setup the router platform."""
    bridge: SynapseBridge = hass.data[DOMAIN][config_entry.entry_id]
    entities = bridge.app_data.get("light")
    if entities is not None:
      async_add_entities(SynapseLight(hass, bridge, entity) for entity in entities)

class SynapseLight(SynapseBaseEntity, LightEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        bridge: SynapseBridge,
        entity: SynapseLightDefinition,
    ):
        super().__init__(hass, bridge, entity)
        self.logger = logging.getLogger(__name__)

    @property
    def is_on(self):
        return self.entity.get("is_on")

    @property
    def brightness(self):
        return self.entity.get("brightness")

    @property
    def color_temp_kelvin(self):
        return self.entity.get("color_temp_kelvin")

    @property
    def supported_features(self):
        return self.entity.get("supported_features")

    @property
    def supported_color_modes(self):
        return self.entity.get("supported_color_modes")

    @property
    def color_mode(self):
        return self.entity.get("color_mode")

    @callback
    async def async_turn_on(self, **kwargs) -> None:
        """Handle turn_on."""
        self.hass.bus.async_fire(
            self.bridge.event_name("turn_on"),
            {"unique_id": self.entity.get("unique_id"), **kwargs},
        )
    
    @callback
    async def async_turn_off(self, **kwargs) -> None:
        """Handle turn_off."""
        self.hass.bus.async_fire(
            self.bridge.event_name("turn_off"),
            {"unique_id": self.entity.get("unique_id"), **kwargs},
        )
