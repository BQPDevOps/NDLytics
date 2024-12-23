from nicegui import ui


class ResolutionsNavbar:
    def __init__(self):
        self.menu_items = [
            {"label": "Pending", "icon": "inbox"},
            {"label": "Resolved", "icon": "check"},
            {"label": "Settings", "icon": "settings"},
        ]

    def on_menu_click(self, e, item):
        print(f"Menu item clicked: {item['label']}")

    def render(self):
        with ui.column().classes("w-full h-full p-4"):
            with ui.card().classes("w-full h-full rounded-lg"):
                with ui.column().classes("w-full h-full"):
                    for item in self.menu_items:
                        ui.button(item["label"]).classes("w-full").props(
                            "flat dense"
                        ).on("click", lambda e: self.on_menu_click(e, item))
