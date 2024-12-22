from nicegui import ui


class ResolutionsNavbar:
    def __init__(self):
        self.menu_items = []

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg"):
                ui.label("Resolutions")
