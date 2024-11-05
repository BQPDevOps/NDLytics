import requests
import pandas as pd
from io import StringIO
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional


class TCNAdapter:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def _send_post(self, url, payload, return_unformatted=False):
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                if return_unformatted:
                    return StringIO(response.text)
                return pd.read_csv(StringIO(response.text))
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def list_campaigns(self, start_datetime, end_datetime):
        url = self.base_url + "/RemoteBroadcastStatusList"
        payload = {
            "accessToken": self.token,
            "startDate": start_datetime,
            "endDate": end_datetime,
        }
        return self._send_post(url, payload)

    def get_report(self, broadcast_id, template_number=4, return_unformatted=False):
        url = self.base_url + "/FtpReportServlet"
        payload = {
            "accessToken": self.token,
            "templateNumber": template_number,
            "taskSid": broadcast_id,
        }
        return self._send_post(url, payload, return_unformatted)

    @staticmethod
    def get_time_range(
        start_date: Optional[str] = None,
        start_time: Optional[str] = None,
        end_date: Optional[str] = None,
        end_time: Optional[str] = None,
        full_day: bool = False,
    ) -> tuple[str, str]:
        pacific_tz = ZoneInfo("America/Los_Angeles")
        current_date = datetime.now(pacific_tz).date()

        if full_day:
            start_datetime = datetime.combine(
                current_date, datetime.min.time()
            ).replace(tzinfo=pacific_tz)
            end_datetime = datetime.combine(current_date, datetime.max.time()).replace(
                tzinfo=pacific_tz
            )
            start_datetime = start_datetime.replace(hour=8, minute=0)
            end_datetime = end_datetime.replace(hour=23, minute=0)
        else:
            if not all([start_date, start_time, end_date, end_time]):
                raise ValueError(
                    "All date and time parameters must be provided when full_day is False"
                )

            start_datetime = datetime.strptime(
                f"{start_date} {start_time}", "%Y-%m-%d %H%M"
            ).replace(tzinfo=pacific_tz)
            end_datetime = datetime.strptime(
                f"{end_date} {end_time}", "%Y-%m-%d %H%M"
            ).replace(tzinfo=pacific_tz)

        formatted_start = start_datetime.strftime("%Y/%m/%d %H:%M")
        formatted_end = end_datetime.strftime("%Y/%m/%d %H:%M")

        return formatted_start, formatted_end

    @staticmethod
    def get_status_code_definitions():
        return {
            1000: "Preparing",
            1100: "Scheduled",
            1200: "Running",
            1210: "Paused",
            1220: "Waiting",
            1300: "Completed",
            1310: "Completed - Timeout",
            1320: "User Canceled",
            1330: "Admin Canceled",
            1400: "Completed - & Billed",
            1410: "Completed - Timeout & Billed",
            1420: "User Canceled & Billed",
            1430: "Admin Canceled & Billed",
            1500: "Completed - & Billed",
            1510: "Completed - Timeout & Billed",
            1520: "User Canceled & Billed",
            1530: "Admin Canceled & Billed",
        }
