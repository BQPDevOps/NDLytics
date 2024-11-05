# components/LiveClock.py
from datetime import datetime
from nicegui import ui
from theme import ThemeManager


class DateTimeDisplay:
    def __init__(self):
        self.theme_manager = ThemeManager()
        with ui.card().tight().classes(
            f"bg-[{self.theme_manager.colors['primary']['highlight']}] gap-0.5 text-white rounded-[0.6rem] shadow-md items-center w-full"
        ):
            self.date_label = ui.label().classes("text-md font-light mb-2")
            with ui.grid(columns=3).classes("w-full border-t border-white gap-0"):
                with ui.column().classes("items-center").style(
                    "border-bottom-left-radius: 0.6rem;border:1px solid white"
                ):
                    self.time_label_hour = ui.label().classes("text-xl font-bold")
                with ui.column().classes("items-center").style(
                    "border:1px solid white;"
                ):
                    self.time_label_minute = ui.label().classes("text-xl font-bold")
                with ui.column().classes("items-center").style(
                    "border-bottom-right-radius: 0.6rem;border:1px solid white"
                ):
                    self.time_label_second = ui.label().classes("text-xl font-bold")
        self.update_time()
        ui.timer(1, self.update_time)

    def update_time(self):
        now = datetime.now()
        date_str = now.strftime("%A, %d %B")
        time_str_hour = now.strftime("%I")  # 12-hour format without AM/PM
        time_str_minute = now.strftime("%M")
        time_str_second = now.strftime("%S")
        # ampm_str = now.strftime("%p")  # AM/PM indicator

        self.date_label.set_text(date_str)
        # self.ampm_label.set_text(ampm_str)
        self.time_label_hour.set_text(time_str_hour)
        self.time_label_minute.set_text(time_str_minute)
        self.time_label_second.set_text(time_str_second)


# class DateTimeDisplay:
#     def __init__(self):
#         self.theme_manager = ThemeManager()
#         with ui.card().classes(
#             f"p-4 bg-[{self.theme_manager.colors['primary']['highlight']}] gap-0.5 text-white rounded-xl shadow-md items-center"
#         ):
#             self.date_label = ui.label().classes("text-md font-light mb-2")
#             with ui.row().classes("items-end"):
#                 self.time_label = ui.label().classes("text-2xl font-bold")
#                 self.ampm_label = ui.label().classes("text-xl font-semibold mr-2")
#         self.update_time()
#         ui.timer(1, self.update_time)

#     def update_time(self):
#         now = datetime.now()
#         date_str = now.strftime("%A, %d %B %Y")
#         time_str = now.strftime("%I:%M:%S")  # 12-hour format without AM/PM
#         ampm_str = now.strftime("%p")  # AM/PM indicator

#         self.date_label.set_text(date_str)
#         self.ampm_label.set_text(ampm_str)
#         self.time_label.set_text(time_str)
