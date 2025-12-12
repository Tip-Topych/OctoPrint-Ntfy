# octoprint_ntfy/__init__.py
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import octoprint.plugin
import requests
import eventlet
from octoprint.events import Events


class NtfyPlugin(octoprint.plugin.StartupPlugin,
                 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.EventHandlerPlugin,
                 octoprint.plugin.TemplatePlugin):

    def on_after_startup(self):
        self._logger.info("Ntfy Plugin загружен! Отправка на: %s/%s" %
                          (self._settings.get(["server_url"]), self._settings.get(["topic"])))

    # --- Настройки ---

    def get_settings_defaults(self):
        return dict(
            server_url="https://ntfy.sh",
            topic="octoprint_alerts",
            access_token="",
            priority="3",  # Default
            # Какие события отслеживать
            event_print_started=True,
            event_print_done=True,
            event_print_failed=True,
            event_print_cancelled=True,
            # Отправлять ли скриншот
            include_snapshot=True
        )

    def get_template_configs(self):
        return [
            dict(type="settings", template="ntfy_settings.jinja2", custom_bindings=False)
        ]

    # --- Обработка событий ---

    def on_event(self, event, payload):
        # Словарь событий и сообщений
        events_map = {
            Events.PRINT_STARTED: ("Печать началась", self._settings.get(["event_print_started"])),
            Events.PRINT_DONE: ("Печать успешно завершена", self._settings.get(["event_print_done"])),
            Events.PRINT_FAILED: ("Ошибка печати", self._settings.get(["event_print_failed"])),
            Events.PRINT_CANCELLED: ("Печать отменена", self._settings.get(["event_print_cancelled"]))
        }

        if event in events_map:
            message_title, is_enabled = events_map[event]

            if is_enabled:
                # Формируем тело сообщения с деталями (имя файла и т.д.)
                file_name = payload.get("name", "Unknown file")
                message_body = f"Файл: {file_name}"

                # Запускаем в отдельном потоке, чтобы не блокировать OctoPrint
                eventlet.spawn_n(self._send_ntfy_notification, message_title, message_body)

    # --- Логика отправки ---

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

        # Если сообщение на русском/юникоде, ntfy лучше принимает его через заголовок при отправке файла
        # или как data при отправке текста. Мы будем отправлять как header X-Message для унификации.
        # Внимание: заголовки HTTP должны быть в Latin-1, поэтому кириллицу лучше кодировать
        # или отправлять текстом. Ntfy поддерживает заголовок "X-Message" в utf-8 (обычно).
        # Но самый надежный способ для ntfy + картинка — это картинка в body, текст в header.

        # Подготавливаем заголовки авторизации
        if token:
            headers["Authorization"] = f"Bearer {token}"

        image_data = None

        # Попытка получить скриншот
        if include_snapshot:
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])
            if snapshot_url:
                try:
                    # Если URL локальный/относительный, добавляем localhost
                    if not snapshot_url.startswith("http"):
                        snapshot_url = f"http://127.0.0.1:8080/{snapshot_url.lstrip('/')}"  # Стандартный порт mjpg-streamer

                    r_img = requests.get(snapshot_url, timeout=5)
                    if r_img.status_code == 200:
                        image_data = r_img.content
                except Exception as e:
                    self._logger.error(f"Не удалось получить снимок: {e}")

        try:
            if image_data:
                # Отправка КАРТИНКИ
                # При отправке файла (binary body), сообщение должно быть в заголовке
                # Ntfy требует кодировку заголовков.
                # Простой requests автоматически кодирует заголовки в latin-1, что ломает кириллицу.
                # Поэтому мы используем base64 кодировку для заголовка Title/Message, если ntfy это поддерживает,
                # либо просто транслит. Но ntfy.sh поддерживает UTF-8 в заголовках.

                # Python requests header trick for UTF-8:
                headers["Message"] = message.encode('utf-8')
                headers["Title"] = title.encode('utf-8')
                headers["Filename"] = "snapshot.jpg"

                requests.put(full_url, data=image_data, headers=headers)
                self._logger.info(f"Отправлено уведомление с фото в ntfy: {title}")

            else:
                # Отправка ТЕКСТА (без картинки)
                headers["Title"] = title.encode('utf-8')
                requests.post(full_url, data=message.encode('utf-8'), headers=headers)
                self._logger.info(f"Отправлено текстовое уведомление в ntfy: {title}")

        except Exception as e:
            self._logger.error(f"Ошибка при отправке в ntfy: {e}")


# Стандартная обвязка для OctoPrint
__plugin_name__ = "Ntfy Notification"
__plugin_pythoncompat__ = ">=3,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = NtfyPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        # Можно добавить хуки обновлений, если нужно, но пока оставим пустым или базовым
    }