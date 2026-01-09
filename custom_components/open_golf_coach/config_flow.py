"""Config flow for Open Golf Coach."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import CONF_NOVA_ENTRY_ID, DOMAIN, NAME

NOVA_DOMAIN = "nova_by_openlaunch"


class OpenGolfCoachConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Open Golf Coach."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        hass: HomeAssistant = self.hass
        nova_entries = hass.config_entries.async_entries(NOVA_DOMAIN)

        if not nova_entries:
            return self.async_abort(reason="no_nova")

        if user_input is not None:
            nova_entry_id = user_input[CONF_NOVA_ENTRY_ID]
            await self.async_set_unique_id(nova_entry_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=NAME,
                data={CONF_NOVA_ENTRY_ID: nova_entry_id},
            )

        if len(nova_entries) == 1:
            nova_entry_id = nova_entries[0].entry_id
            await self.async_set_unique_id(nova_entry_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=NAME,
                data={CONF_NOVA_ENTRY_ID: nova_entry_id},
            )

        options = {entry.entry_id: entry.title for entry in nova_entries}
        schema = vol.Schema({vol.Required(CONF_NOVA_ENTRY_ID): vol.In(options)})
        return self.async_show_form(step_id="user", data_schema=schema)
