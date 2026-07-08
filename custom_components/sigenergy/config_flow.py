"""Config flow for Sigenergy integration."""

import logging
from typing import Any, Dict, Optional

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SigenergySomeClient,
    SigenergySomeInvalidAuth,
    SigenergySomeConnectionError,
    SigenergySomeAPIError,
)
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

_LOGGER = logging.getLogger(__name__)


async def validate_auth(
    hass: HomeAssistant,
    username: str,
    password: str,
    account_id: Optional[str] = None,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate Sigenergy credentials."""
    session = async_get_clientsession(hass)
    api_client = SigenergySomeClient(
        session=session,
        username=username,
        password=password,
        account_id=account_id,
        api_key=api_key,
        client_id=client_id,
        client_secret=client_secret,
    )

    try:
        await api_client.authenticate()
        systems = await api_client.get_systems()
        await api_client.close()
        return {
            "title_placeholders": {
                "name": f"Sigenergy ({username})",
            }
        }
    except SigenergySomeInvalidAuth as err:
        raise InvalidAuth from err
    except SigenergySomeConnectionError as err:
        raise CannotConnect from err


class SigenergySomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Sigenergy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle a user initiated config flow."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_auth(
                    self.hass,
                    user_input.get(CONF_CLIENT_ID),
                    user_input.get(CONF_CLIENT_SECRET),
                )

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
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_ACCOUNT_ID): str,
                    vol.Optional(CONF_API_KEY): str,
                    vol.Optional(CONF_CLIENT_ID): str,
                                        vol.Optional(CONF_ENERGY_FLOW_INTERVAL, default=ENERGY_FLOW_INTERVAL): int,
                                        vol.Optional(CONF_SUMMARY_INTERVAL, default=SUMMARY_INTERVAL): int,
                    vol.Optional(CONF_CLIENT_SECRET
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_ACCOUNT_ID): str,
                    vol.Optional(CONF_API_KEY): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "documentation_url": "https://developer.sigencloud.com/user/api/document/17",
            },
        )


class InvalidAuth(HomeAssistantError):
    """Exception for invalid authentication."""


class CannotConnect(HomeAssistantError):
    """Exception for cannot connect error."""
