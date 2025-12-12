# octoprint_ntfy/__init__.py
# -*- coding: utf-8 -*-
from __future__ import absolute_import

from octoprint.plugin import (
    StartupPlugin,
    SettingsPlugin,
    EventHandlerPlugin,
    TemplatePlugin,
    SimpleApiPlugin  # Добавили SimpleApiPlugin
)
import requests
import eventlet
from octoprint.events import Events


class NtfyPlugin(StartupPlugin,
                 SettingsPlugin,
                 EventHandlerPlugin,
                 TemplatePlugin,
                 SimpleApiPlugin):  # Добавили SimpleApiPlugin

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

    def on_api_command(self, command, data):
        if command == "send_test_notification":
            self._logger.info("Отправка тестового уведомления...")
            eventlet.spawn_n(self._send_ntfy_notification, "Тестовое уведомление", "Это тестовое уведомление от плагина OctoPrint-Ntfy.")

    def _send_ntfy_notification(self, title, message):
        server_url = self._settings.get(["server_url"]).rstrip('/')
        topic = self._settings.get(["topic"])
        token = self._settings.get(["access_token"])
        priority = self._settings.get(["priority"])
        include_snapshot = self._settings.get_boolean(["include_snapshot"])

        full_url = f"{server_url}/{topic}"

        headers = {
            "Title": title.encode('utf-8'),
            "Priority": priority,
            "Tags": "printer"
        }

        if token:
            headers["Authorization"] = f"Bearer {token}"

        image_data = None

        if include_snapshot:
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])
            if snapshot_url:
                try:
                    if not snapshot_url.startswith("http"):
                        snapshot_url = f"http://127.0.0.1:8080/{snapshot_url.lstrip('/')}"

                    r_img = requests.get(snapshot_url, timeout=5)
                    if r_img.status_code == 200:
                        image_data = r_img.content
                except Exception as e:
                    self._logger.error(f"Не удалось получить снимок: {e}")

        try:
            if image_data:
                headers["Message"] = message.encode('utf-8')
                headers["Title"] = title.encode('utf-8')
                headers["Filename"] = "snapshot.jpg"
                requests.put(full_url, data=image_data, headers=headers)
                self._logger.info(f"Отправлено уведомление с фото в ntfy: {title}")
            else:
                headers["Title"] = title.encode('utf-8')
                requests.post(full_url, data=message.encode('utf-8'), headers=headers)
                self._logger.info(f"Отправлено текстовое уведомление в ntfy: {title}")
        except Exception as e:
            self._logger.error(f"Ошибка при отправке в ntfy: {e}")

    # --- SoftwareUpdatePlugin implementation ---
    def get_update_information(self):
        return dict(
            ntfy=dict(
                displayName="Ntfy Plugin",
                displayVersion=self._plugin_version,
                type="github_release",
                user="Tip-Topych",
                repo="OctoPrint-Ntfy",
                current=self._plugin_version,
                pip="https://github.com/Tip-Topych/OctoPrint-Ntfy/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "Ntfy Notification"
__plugin_version__ = "1.0.0"
__plugin_description__ = "A plugin to send notifications to a ntfy server."
__plugin_author__ = "Padla"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = NtfyPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
