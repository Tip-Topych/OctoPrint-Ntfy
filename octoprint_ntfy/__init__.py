# octoprint_ntfy/__init__.py
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import octoprint.plugin
import requests
import eventlet
from octoprint.events import Events

# Убрали несуществующий SoftwareUpdatePlugin из наследования
class NtfyPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.EventHandlerPlugin,
                 octoprint.plugin.TemplatePlugin):

    def on_after_startup(self):
        self._logger.info("Ntfy Plugin загружен!")

    def get_settings_defaults(self):
        return dict(
            server_url="https://ntfy.sh",
            topic="octoprint_alerts",
            access_token="",
            priority="3",
            event_print_started=True,
            event_print_done=True,
            event_print_failed=True,
            event_print_cancelled=True,
            include_snapshot=True
        )

    def get_template_configs(self):
        return [
            # Явно указываем имя файла шаблона
            dict(type="settings", template="ntfy_settings.jinja2", custom_bindings=False)
        ]

    def on_event(self, event, payload):
        events_map = {
            Events.PRINT_STARTED: ("Печать началась", self._settings.get(["event_print_started"])),
            Events.PRINT_DONE: ("Печать успешно завершена", self._settings.get(["event_print_done"])),
            Events.PRINT_FAILED: ("Ошибка печати", self._settings.get(["event_print_failed"])),
            Events.PRINT_CANCELLED: ("Печать отменена", self._settings.get(["event_print_cancelled"]))
        }

        if event in events_map:
            message_title, is_enabled = events_map[event]
            if is_enabled:
                file_name = payload.get("name", "Unknown file")
                message_body = f"Файл: {file_name}"
                eventlet.spawn_n(self._send_ntfy_notification, message_title, message_body)

    def _send_ntfy_notification(self, title, message):
        # ... (ваш код отправки, который был ранее) ...
        pass

__plugin_name__ = "Ntfy Notification"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = NtfyPlugin()

    global __plugin_hooks__
    # ОСТАВЛЯЕМ ПУСТЫМ, чтобы не вызывать ошибок обновлений
    __plugin_hooks__ = {}