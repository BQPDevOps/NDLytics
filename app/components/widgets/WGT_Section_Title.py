from nicegui import ui


class WGT_Section_Title:
    def __init__(self, widget_configuration=None, widget_instance_id=None):
        self.widget_configuration = (
            widget_configuration or {}
        )  # Default to empty dict if None
        self.widget_instance_id = widget_instance_id
        self.widget_width = self.widget_configuration.get("widget_width", 10)
        self.widget_id = "wgt_section_title"
        self.widget_name = "Section Title"
        self.widget_description = "Displays a section title with a separator"
        self.widget_icon = "title"

        self.widget_container = None

        self._set_default_configuration()

    def _set_default_configuration(self):
        if not self.widget_configuration:
            self.widget_configuration = {
                "title": "Section Title",
                "title_color": "black",
                "title_size": "1.5rem",
                "separator_color": "gray",
                "separator_style": "solid",
                "separator_width": "1px",
                "widget_width": 10,
            }

    def widget_configuration_form(self):
        with ui.column().style("display:flex;width:100%;height:100%"):
            ui.input(
                label="Title",
                value=self.widget_configuration["title"],
                on_change=lambda e: self._update_configuration("title", e.value),
            ).style("width:100%")
            ui.color_input(
                label="Title Color",
                value=self.widget_configuration["title_color"],
                on_change=lambda e: self._update_configuration("title_color", e.value),
            )
            ui.input(
                label="Title Size",
                value=self.widget_configuration["title_size"],
                on_change=lambda e: self._update_configuration("title_size", e.value),
            ).style("width:100%")
            ui.color_input(
                label="Separator Color",
                value=self.widget_configuration["separator_color"],
                on_change=lambda e: self._update_configuration(
                    "separator_color", e.value
                ),
            )
            ui.select(
                label="Separator Style",
                options=["solid", "dashed", "dotted"],
                value=self.widget_configuration["separator_style"],
                on_change=lambda e: self._update_configuration(
                    "separator_style", e.value
                ),
            ).style("width:100%")
            ui.input(
                label="Separator Width",
                value=self.widget_configuration["separator_width"],
                on_change=lambda e: self._update_configuration(
                    "separator_width", e.value
                ),
            ).style("width:100%")

    def _update_configuration(self, key, value):
        self.widget_configuration[key] = value
        self.create_widget()

    def create_widget(self, widget_configuration=None):
        if widget_configuration:
            self.widget_configuration = widget_configuration
            self.widget_width = widget_configuration.get(
                "widget_width", self.widget_width
            )
            self._set_default_configuration()

        if not self.widget_container:
            with ui.column().classes("w-full") as container:
                self.widget_container = container

        self.widget_container.clear()

        with self.widget_container:
            with ui.row().style("display:flex;flex-direction:row;width:100%; gap:0"):
                ui.label(self.widget_configuration["title"]).style(
                    f"font-size: {self.widget_configuration['title_size']}; "
                    f"font-weight: bold; "
                    f"color: {self.widget_configuration['title_color']};"
                )
                ui.separator().style(
                    f"border-top: {self.widget_configuration['separator_width']} "
                    f"{self.widget_configuration['separator_style']} "
                    f"{self.widget_configuration['separator_color']};"
                )

    def get_widget_details(self):
        return {
            "widget_id": self.widget_id,
            "widget_instance_id": self.widget_instance_id,
            "widget_name": self.widget_name,
            "widget_description": self.widget_description,
            "widget_configuration": self.widget_configuration,
        }
