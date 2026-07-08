"""The Sigenergy integration."""

from __future__ import annotations

from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SigenergyClient
from .const import (
    CONF_ACCOUNT_ID,
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_ENERGY_FLOW_INTERVAL,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_SUMMARY_INTERVAL,
    CONF_USERNAME,
    DOMAIN,
    ENERGY_FLOW_INTERVAL,
    REGION_EU,
    REGION_URLS,
    SUMMARY_INTERVAL,
)
from .coordinator import SigenergyDataUpdateCoordinator

PLATFORMS: Final = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sigenergy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = SigenergyClient(
        session=async_get_clientsession(hass),
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        account_id=entry.data.get(CONF_ACCOUNT_ID),
        api_key=entry.data.get(CONF_API_KEY),
        client_id=entry.data.get(CONF_CLIENT_ID),
        client_secret=entry.data.get(CONF_CLIENT_SECRET),
        base_url=REGION_URLS.get(entry.data.get(CONF_REGION, REGION_EU), REGION_URLS[REGION_EU]),
    )

    coordinator = SigenergyDataUpdateCoordinator(
        hass,
        client,
        energy_flow_interval=int(entry.data.get(CONF_ENERGY_FLOW_INTERVAL, ENERGY_FLOW_INTERVAL)),
        summary_interval=int(entry.data.get(CONF_SUMMARY_INTERVAL, SUMMARY_INTERVAL)),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Sigenergy config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
