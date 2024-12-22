from nicegui import ui


class ReportsContainer:
    def __init__(self):
        self.navbar = ui.navbar()

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg"):
                ui.label("Reports")
