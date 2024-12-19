from io import StringIO
from nicegui import ui
import requests
import pandas as pd
from icecream import ic
from config import config


class TNCMiddleware:
    def __init__(self):
        self.status_webhook_url = config.n8n_get_task_group_status_webhook
        self.outbound_reporting_webhook_url = config.n8n_get_outbound_reporting_webhook

    def _send_get(self, url, return_unformatted=False):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                if return_unformatted:
                    return StringIO(response.text)
                return pd.read_csv(StringIO(response.text))
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def get_task_group(self):
        url = self.status_webhook_url
        return self._send_get(url)

    def get_outbound_reporting(self):
        url = self.outbound_reporting_webhook_url
        return self._send_get(url)


class CampaignsViewArea:
    def __init__(self):
        self.tnc_middleware = TNCMiddleware()
        self._on_page_load()

    def _on_page_load(self):
        self.outbound_reporting = self.tnc_middleware.get_outbound_reporting()
        ic(self.outbound_reporting)

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg"):
                with ui.grid(columns=2).classes("w-full h-full"):
                    with ui.column().classes("col-span-1"):
                        ui.label("Campaigns")
                    with ui.column().classes("col-span-1"):
                        ui.label("Campaigns")
