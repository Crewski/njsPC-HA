"""Config flow for njsPC-HA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client
from homeassistant.components import zeroconf, ssdp
from urllib.parse import urlparse


from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=4200): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    session = aiohttp_client.async_get_clientsession(hass)
    async with session.get(f'http://{data["host"]}:{data["port"]}/state/all') as resp:
        if resp.status == 200:
            pass
        else:
            raise CannotConnect

    return {"title": "njsPC-HA"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for njsPC-HA."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.zero_conf = None
        self.host = None
        self.port = None
        self.server_id = None
        self.controller_name = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
            self.server_id = f'njspcha_{user_input[CONF_HOST].replace(".", "")}{user_input[CONF_PORT]}'
            await self.async_set_unique_id(self.server_id)
            self._abort_if_unique_id_configured()
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        self.zero_conf = discovery_info
        self.server_id = (
            f'njspcha_{discovery_info.host.replace(".", "")}{discovery_info.port}'
        )
        # Do not probe the device if the host is already configured
        self._async_abort_entries_match(self.server_id)

        # Check if already configured
        await self.async_set_unique_id(self.server_id)
        self._abort_if_unique_id_configured()
        self.context.update(
            {
                "title_placeholders": {
                    CONF_HOST: discovery_info.host,
                    CONF_PORT: discovery_info.port,
                },
            }
        )
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] = None
    ) -> FlowResult:
        """Handle a flow initiated by zeroconf."""
        if user_input is not None:
            data = {
                CONF_HOST: self.zero_conf.host,
                CONF_PORT: self.zero_conf.port,
            }
            return self.async_create_entry(title="njsPC-HA", data=data)
        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                CONF_HOST: self.zero_conf.host,
                CONF_PORT: self.zero_conf.port,
            },
        )

    async def async_step_ssdp(self, discovery_info: ssdp.SsdpServiceInfo) -> FlowResult:
        """Handle a flow initialized by SSDP discovery."""
        self.host = urlparse(discovery_info.ssdp_location).hostname
        self.port = urlparse(discovery_info.ssdp_location).port
        self.server_id = f'njspcha_{self.host.replace(".", "")}{self.port}'
        await self.async_set_unique_id(self.server_id)
        self._abort_if_unique_id_configured()
        self.controller_name = discovery_info.upnp.get(
            ssdp.ATTR_UPNP_FRIENDLY_NAME, self.host
        )
        self.context.update(
            {
                "title_placeholders": {
                    "name": self.controller_name,
                    CONF_HOST: self.host,
                    CONF_PORT: self.port,
                },
            }
        )
        return await self.async_step_ssdp_confirm()

    async def async_step_ssdp_confirm(
        self, user_input: dict[str, Any] = None
    ) -> FlowResult:
        """Handle a flow initiated by zeroconf."""
        if user_input is not None:
            data = {
                CONF_HOST: self.host,
                CONF_PORT: self.port,
            }
            return self.async_create_entry(title="njsPC-HA", data=data)
        return self.async_show_form(
            step_id="ssdp_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "name": self.controller_name,
                CONF_HOST: self.host,
                CONF_PORT: self.port,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
