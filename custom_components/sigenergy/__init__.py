"""The Sigenergy integration."""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SigenergySomeClient
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_ACCOUNT_ID,
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ENERGY_FLOW_INTERVAL,
    CONF_SUMMARY_INTERVAL,
    ENERGY_FLOW_INTERVAL,
    SUMMARY_INTERVAL,
)
from .coordinator import SigenergySomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.SENSOR, Platform.SWITCH, Platform.BINARY_SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sigenergy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api_client = SigenergySomeClient(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        account_id=entry.data.get(CONF_ACCOUNT_ID),
        api_key=entry.data.get(CONF_API_KEY),
        client_id=entry.data.get(CONF_CLIENT_ID),
        client_secret=entry.data.get(CONF_CLIENT_SECRET),
    )

    coordinator = SigenergySomeDataUpdateCoordinator(hass, api_client)
    await coordinator.async_config_entry_first_refresh()

    # Apply frequency configuration
    coordinator.energy_flow_interval = entry.data.get(
        CONF_ENERGY_FLOW_INTERVAL, ENERGY_FLOW_INTERVAL
    )
    coordinator.summary_interval = entry.data.get(
        CONF_SUMMARY_INTERVAL, SUMMARY_INTERVAL
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "api_client": api_client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        data = hass.data[DOMAIN].pop(entry.entry_id)
        api_client = data["api_client"]
        await api_client.close()

    return unload_ok
