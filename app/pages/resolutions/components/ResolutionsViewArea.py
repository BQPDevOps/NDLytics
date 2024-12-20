from nicegui import ui


class ResolutionsViewArea:
    def __init__(self):
        pass

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg"):
                ui.label("View Area")
