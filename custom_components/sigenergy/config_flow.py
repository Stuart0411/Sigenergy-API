"""Config flow for Sigenergy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SigenergyApiError,
    SigenergyClient,
    SigenergyConnectionError,
    SigenergyInvalidAuth,
)
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
    REGION_ANZ,
    REGION_AP,
    REGION_CN,
    REGION_EU,
    REGION_JP,
    REGION_LA,
    REGION_MEA,
    REGION_NA,
    REGION_URLS,
    SUMMARY_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> None:
    """Validate provided credentials."""
    client = SigenergyClient(
        session=async_get_clientsession(hass),
        username=user_input[CONF_USERNAME],
        password=user_input[CONF_PASSWORD],
        account_id=user_input.get(CONF_ACCOUNT_ID),
        api_key=user_input.get(CONF_API_KEY),
        client_id=user_input.get(CONF_CLIENT_ID),
        client_secret=user_input.get(CONF_CLIENT_SECRET),
        base_url=REGION_URLS[user_input[CONF_REGION]],
    )

    try:
        await client.authenticate()
        await client.get_systems()
    except SigenergyInvalidAuth as err:
        raise InvalidAuth from err
    except SigenergyConnectionError as err:
        raise CannotConnect from err
    except SigenergyApiError as err:
        # Most API errors during validation are auth/provisioning related.
        raise InvalidAuth from err


class SigenergyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sigenergy."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)

                await self.async_set_unique_id(
                    f"{user_input[CONF_USERNAME]}_{user_input.get(CONF_ACCOUNT_ID, 'default')}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Sigenergy ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REGION, default=REGION_EU): vol.In(
                        {
                            REGION_EU: "Europe",
                            REGION_AP: "Asia Pacific & Middle Asia",
                            REGION_MEA: "Middle East & Africa",
                            REGION_CN: "Chinese Mainland",
                            REGION_ANZ: "Australia & New Zealand",
                            REGION_LA: "Latin America",
                            REGION_NA: "North America",
                            REGION_JP: "Japan",
                        }
                    ),
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_ACCOUNT_ID): str,
                    vol.Optional(CONF_API_KEY): str,
                    vol.Optional(CONF_CLIENT_ID): str,
                    vol.Optional(CONF_CLIENT_SECRET): str,
                    vol.Optional(CONF_ENERGY_FLOW_INTERVAL, default=ENERGY_FLOW_INTERVAL): vol.All(
                        vol.Coerce(int), vol.Range(min=300)
                    ),
                    vol.Optional(CONF_SUMMARY_INTERVAL, default=SUMMARY_INTERVAL): vol.All(
                        vol.Coerce(int), vol.Range(min=300)
                    ),
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
