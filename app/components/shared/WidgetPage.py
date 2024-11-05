# shared/WidgetPage.py
import uuid
import math

import boto3
from nicegui import ui

from components.common import DateTimeDisplay
from utils.helpers import cognito_adapter, gateway_adapter, s3_storage_adapter
from utils.lists import get_list
from theme import ThemeManager

from components.widgets import *


class WidgetPage:
    def __init__(
        self,
        page_title: str,
        page_route: str,
        page_description: str,
        tag_name: str,
        storage_manager,
        creator_presets,
    ):
        self.theme_manager = ThemeManager()
        self.page_title = page_title
        self.page_route = page_route
        self.page_description = page_description
        self.tag_name = tag_name
        self.dynamo_db = None
        self.dynamo_table = None
        self.storage = storage_manager
        self.cognito_adapter = cognito_adapter()
        self.gateway_adapter = gateway_adapter(storage_manager)
        self.s3_adapter = s3_storage_adapter(storage_manager)
        self.page_widget_layout_configuration = []
        self.page_mode = "view"
        self.df_store = {}
        self.creator_widget_preview = None
        self.creator_step = 0
        self.creator_presets = creator_presets

        self.layout_widget_id = (
            f'{self.page_title.lower().replace(" ", "_")}_page_config'
        )

        self.toolbar_items = {
            "menu": {
                "icon": "menu",
                "color": "blue",
                "direction": "left",
            },
            "submenu": [
                {
                    "icon": "o_logout",
                    "color": "blue-5",
                    "callback": lambda: self.cognito_adapter.signout(),
                },
                {
                    "icon": "o_construction",
                    "color": "green-5",
                    "callback": lambda: self.toggle_edit_mode(),
                },
            ],
        }

        self.navigation_items = get_list("page_routes")
        self._onload()

    def _onload(self):
        self.dynamo_db = boto3.resource("dynamodb", region_name="us-east-1")
        self.dynamo_table = self.dynamo_db.Table("NDA_Settings_Table")

    def get_dataframe(self, file_key):
        """Retrieve a DataFrame from the store or load it from S3."""
        if file_key not in self.df_store:
            self.df_store[file_key] = self.s3_adapter.read_csv_to_dataframe(
                bucket_name="nda-storage-v1", file_key=file_key
            )
        return self.df_store[file_key]

    def get_widget_by_id(
        self, widget_id, widget_configuration=None, widget_instance_id=None
    ):
        """
        Instantiates the widget component by its ID.
        Widgets are responsible for their own data fetching and rendering.
        """
        # Ensure widget_configuration is always a dictionary
        widget_configuration = widget_configuration or {}

        widget_map = {
            "wgt_section_title": WGT_Section_Title,
            "wgt_growth_metrics": WGT_Growth_Metrics,
            "wgt_operator_performance_analysis": WGT_Operator_Performance_Analysis,
            "wgt_yearly_collections_comparison": WGT_Yearly_Collections_Comparison,
            "wgt_mtd_collections": WGT_MTD_Collections,
            "wgt_prior_month_collections": WGT_Prior_Month_Collections,
            "wgt_call_duration_analysis": WGT_Call_Duration_Analysis,
            "wgt_call_outcome_analysis": WGT_Call_Outcome_Analysis,
        }

        widget_class = widget_map.get(widget_id)
        if widget_class:
            if widget_id == "wgt_section_title":
                return widget_class(widget_configuration, widget_instance_id)
            else:
                return widget_class(
                    self.get_dataframe, widget_configuration, widget_instance_id
                )
        else:
            print(f"Unknown widget ID: {widget_id}")
            return None

    def set_creator_widget_preview(self, widget_id: str):
        self.creator_widget_preview = self.get_widget_by_id(widget_id)

    def set_creator_step(self, step: int):
        self.creator_step = step

    def set_page_mode(self, mode: str):
        self.page_mode = mode

    def get_widget_layout_configuration(self):
        try:
            response = self.dynamo_table.get_item(
                Key={
                    "uuid": self.cognito_adapter.get_user_id(),
                    "tag": self.tag_name,
                }
            )
            item = response.get("Item")
            if item and "configured_page_widgets" in item:
                self.page_widget_layout_configuration = item["configured_page_widgets"]
                return self.page_widget_layout_configuration
            else:
                ui.notify("No page layout found for this user.")
                return []
        except Exception as e:
            print(f"Error fetching page layout: {e}")
            return []

    def render_sidebar_navigation(self):
        with ui.left_drawer(top_corner=True, bottom_corner=True).style(
            # f"background-color: {self.theme_manager.colors['primary']['base']}; width: 240px !important;"
            f"background: linear-gradient(22deg, rgba(0,68,102,1) 0%, rgba(0,68,102,1) 30%, rgba(0,131,196,1) 86%, rgba(0,90,135,1) 93%, rgba(0,82,124,1) 100%); width: 240px !important;"
        ):
            with ui.column().classes("flex h-screen w-full"):
                with ui.row().classes("flex justify-start items-center w-full"):
                    with ui.row().classes(
                        "w-full flex justify-center items-center"
                    ).style(
                        f"overflow:hidden;background-color: transparent;"
                        # f"overflow:hidden;background-color: white; border: 1px solid white; border-radius: 8px;"
                    ):
                        ui.image(
                            "static/images/branding/ndlytics_logo_dark.svg"
                            # "static/images/branding/ndlytics_logo_light.svg"
                        ).classes("w-2/3").style("height:40px;")
                    # with ui.row().classes("flex justify-center items-center w-full"):
                    #     DateTimeDisplay()
                    with ui.row().classes("flex justify-start items-center w-full"):
                        with ui.list().props("bordered separator").classes(
                            "w-full rounded-lg"
                        ):
                            for index, section in enumerate(self.navigation_items):
                                page_name = section["page_name"]
                                route = section["route"]
                                icon = section["icon"]
                                required_permissions = section.get(
                                    "required_permissions", []
                                )

                                if (
                                    not required_permissions
                                    or self.cognito_adapter.has_permission(
                                        required_permissions
                                    )
                                ):
                                    selected = self.page_route == route

                                    bg_color = (
                                        f"{self.theme_manager.colors['primary']['highlight']}"
                                        if selected
                                        else f"{self.theme_manager.colors['secondary']['base']}"
                                    )
                                    box_shadow = (
                                        "inset 0 0 10px rgba(255, 255, 255, 0.3)"
                                        if selected
                                        else ""
                                    )

                                    # Determine border radius based on visible items
                                    if index == 0:
                                        border_radius = "10px 10px 0 0"
                                    elif index == len(self.navigation_items) - 1:
                                        border_radius = "0 0 10px 10px"
                                    else:
                                        border_radius = "0"

                                    with ui.item(
                                        on_click=lambda p=route: ui.navigate.to(p)
                                    ).style(
                                        f"background-color: {bg_color}; color: white; box-shadow: {box_shadow}; border-radius: {border_radius};"
                                    ):
                                        with ui.item_section():
                                            ui.icon(icon)
                                        with ui.item_section():
                                            ui.item_label(page_name).style(
                                                f"color: {self.theme_manager.colors['text']['base']}"
                                            )
                                else:
                                    # Debugging: Permission denied for this section
                                    print(f"Permission denied for section: {page_name}")

    def render_toolbar(self):
        primary_menu = self.toolbar_items.get("menu")
        secondary_menu = self.toolbar_items.get("submenu")

        with ui.header().style("background-color:#EEF4FA"):
            with ui.row().classes("flex w-full"):
                ui.space()
                with ui.element("q-fab").props(
                    f"icon={primary_menu['icon']} color={primary_menu['color']} direction={primary_menu['direction']}"
                ):
                    for item in secondary_menu:
                        ui.element("q-fab-action").props(
                            f"icon={item['icon']} color={item['color']}"
                        ).on("click", item["callback"])
            ui.separator()

    def toggle_edit_mode(self):
        """Toggle between edit and display modes."""
        if self.page_mode == "edit":
            self.set_page_mode("view")
        else:
            self.set_page_mode("edit")
        self.render_widgets.refresh()

    def toggle_widget_create_mode(self):
        """Toggle widget create mode."""
        self.set_page_mode("create")
        self.render_widgets.refresh()

    @ui.refreshable
    def render_widget_creator_preview(self):
        """Renders the widget creator with the updated configuration."""
        if self.creator_widget_preview:
            self.creator_widget_preview.create_widget()
        else:
            ui.label("No widget selected for preview.")

    def handle_preset_widget_selection(self, widget_id):
        """Handles the selection of a preset widget."""
        self.creator_widget_preview = self.get_widget_by_id(widget_id)
        if self.creator_widget_preview:
            self.render_widget_creator.refresh()

    @ui.refreshable
    def render_configuration_step(self):
        """Renders the widget configuration step."""
        if self.creator_widget_preview:
            self.creator_widget_preview.widget_configuration_form()
        else:
            ui.label("No widget selected for configuration.")

    @ui.refreshable
    def render_widget_creator(self):
        with ui.row().style("display:flex;flex:1;height:85vh;width:100%"):
            with ui.column().style(
                "display:flex;flex:2;width:50%;height:85vh;justify-content:center;align-items:center"
            ):
                self.render_widget_creator_preview()

            # Right column for widget selection and configuration
            with ui.column().style("display:flex;flex:1;width:50%;height:85vh"):
                with ui.stepper().props("horizontal").classes(
                    "w-full h-full"
                ) as stepper:
                    # Step 1: Select Widget
                    with ui.step("Select Widget"):
                        with ui.scroll_area().style("width:100%;height:100%"):
                            with ui.list().props("bordered separator").style(
                                "width:100%"
                            ):
                                for widget in self.creator_presets:
                                    widget_instance = self.get_widget_by_id(
                                        widget["widget_id"]
                                    )
                                    widget_details = (
                                        widget_instance.get_widget_details()
                                    )
                                    with ui.item():
                                        with ui.item_section().style(
                                            "display:flex;flex-direction:column;justify-content:center;"
                                        ):
                                            ui.item_label(
                                                widget_details["widget_name"]
                                            ).classes("text-lg font-bold")
                                            ui.item_label(
                                                widget_details["widget_description"]
                                            ).props("caption")
                                        ui.space()
                                        with ui.item_section().style(
                                            "display:flex;justify-content:center;align-items:flex-end"
                                        ):
                                            ui.button(
                                                "Select",
                                                on_click=lambda w=widget[
                                                    "widget_id"
                                                ]: self.handle_preset_widget_selection(
                                                    w
                                                ),
                                            ).style("width:30%;text-align:right")

                        with ui.column().style(
                            "flex-direction:row;display:flex;width:100%;align-items:flex-end"
                        ):
                            ui.button("Cancel", on_click=self.toggle_edit_mode)
                            ui.space()
                            with ui.stepper_navigation():
                                ui.button("Next").on("click", stepper.next)

                    # Step 2: Configure Widget
                    with ui.step("Configure Widget"):
                        if self.creator_widget_preview:
                            self.creator_widget_preview.widget_configuration_form()
                        else:
                            ui.label("No widget selected for configuration.")
                        with ui.stepper_navigation().style(
                            "display:flex;height:100%;width:100%"
                        ):
                            with ui.row().classes(
                                "w-full h-full justify-between items-end"
                            ):
                                ui.button("Back").on("click", stepper.previous)
                                ui.button(
                                    "Finish",
                                    on_click=(lambda: self.add_widget_to_layout()),
                                )

    def add_widget_to_layout(self):
        """Add the widget to the user's layout preferences."""
        if self.creator_widget_preview:
            widget = self.creator_widget_preview.get_widget_details()
            if widget["widget_instance_id"] is None:
                ui.notify("Adding widget to layout...")
                widget["widget_instance_id"] = self.generate_widget_id()
                widget["widget_width"] = 5  # Default to half width
                self.page_widget_layout_configuration.append(widget)
            else:
                self.update_configured_page_layout(
                    widget["widget_instance_id"],
                    "widget_configuration",
                    widget["widget_configuration"],
                )
            self.set_page_mode("edit")
        else:
            ui.notify("No widget selected for addition.")
        self.render_widgets.refresh()

    def update_configured_page_layout(self, widget_instance_id, key, value):
        widget_list = self.page_widget_layout_configuration
        for widget in widget_list:
            if widget.get("widget_instance_id") == widget_instance_id:
                widget[key] = value
                break  # Exit the loop once the widget is found and updated
        self.page_widget_layout_configuration = widget_list

    def generate_widget_id(self):
        """Generates a random widget_id to avoid duplicates."""
        return str(uuid.uuid4())  # Use UUID to generate unique IDs

    def calculate_layout(self, widgets, total_width=10):
        rows = []
        current_row = []
        current_width = 0

        for widget in widgets:
            widget_instance = self.get_widget_by_id(
                widget["widget_id"],
                widget["widget_configuration"],
                widget["widget_instance_id"],
            )
            widget_width = getattr(
                widget_instance, "width", 5
            )  # Default to 5 if width is not set
            if current_width + widget_width > total_width:
                # Start a new row
                rows.append(current_row)
                current_row = [widget]
                current_width = widget_width
            else:
                current_row.append(widget)
                current_width += widget_width

        # Add the last row if it's not empty
        if current_row:
            rows.append(current_row)

        return rows

    @ui.refreshable
    def render_widgets(self):
        """Renders widgets based on their specified widths."""
        if self.page_mode == "create":
            self.render_widget_creator()
            return

        # Add the "Add Widget" button at the top when in edit mode
        if self.page_mode == "edit":
            with ui.row().classes("w-full justify-end"):
                ui.button("Add Widget", on_click=self.toggle_widget_create_mode)
                ui.button("Save Layout", on_click=lambda: self.save_layout())

        # Calculate the layout
        layout = self.calculate_layout(self.page_widget_layout_configuration)

        # Render the layout
        for row in layout:
            with ui.row().classes("w-full flex flex-wrap -mx-2"):
                for widget_info in row:
                    try:
                        widget_instance = self.get_widget_by_id(
                            widget_info["widget_id"],
                            widget_info["widget_configuration"],
                            widget_info["widget_instance_id"],
                        )
                        if widget_instance is None:
                            print(
                                f"Widget with ID {widget_info['widget_id']} not found. Skipping."
                            )
                            continue

                        widget_width = getattr(
                            widget_instance, "widget_width", 5
                        )  # Default to 5 if width is not set
                        percentage_width = math.floor((widget_width / 11) * 100)
                        with ui.column().classes(f"p-2").style(
                            f"width: {percentage_width}%;"
                        ):
                            container_styling = "background-color:transparent;border:none;padding:0;box-shadow:none;"
                            with ui.card().style(container_styling).classes(
                                "w-full h-full"
                            ).tight():
                                if self.page_mode == "edit":
                                    self.render_widget_edit_mode(
                                        self.page_widget_layout_configuration.index(
                                            widget_info
                                        ),
                                        widget_info,
                                    )
                                else:
                                    self.render_widget_display_mode(widget_info)
                    except Exception as e:
                        print(
                            f"Error rendering widget {widget_info['widget_id']}: {str(e)}. Skipping."
                        )
                        continue

    def render_widget_display_mode(self, widget_info):
        """Renders the widget in display mode."""
        widget = self.get_widget_by_id(
            widget_info["widget_id"],
            widget_info["widget_configuration"],
            widget_info["widget_instance_id"],
        )
        if widget:
            with ui.card_section().classes("w-full h-full"):
                widget.create_widget(widget_info["widget_configuration"])
        else:
            print(f"Skipping widget with ID: {widget_info['widget_id']}")

    def render_widget_edit_mode(self, index, widget_info):
        """Renders the widget with edit controls (move, delete)."""
        widget = self.get_widget_by_id(
            widget_info["widget_id"],
            widget_info["widget_configuration"],
            widget_info["widget_instance_id"],
        )

        def decrease_width():
            if widget.widget_width > 1:
                widget.widget_width -= 1
                widget_info["widget_configuration"][
                    "widget_width"
                ] = widget.widget_width
                self.render_widgets.refresh()

        def increase_width():
            if widget.widget_width < 10:
                widget.widget_width += 1
                widget_info["widget_configuration"][
                    "widget_width"
                ] = widget.widget_width
                self.render_widgets.refresh()

        with ui.card_section().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center"):
                with ui.row().classes("items-center gap-2"):
                    ui.button(icon="remove", on_click=decrease_width).props(
                        "round flat dense"
                    ).classes("text-grey-8")

                    ui.label(f"Width: {widget.widget_width}").classes("text-body1")

                    ui.button(icon="add", on_click=increase_width).props(
                        "round flat dense"
                    ).classes("text-grey-8")

                with ui.row():
                    ui.button(
                        icon="arrow_back", on_click=lambda: self.move_widget_left(index)
                    ).props("round glossy")
                    ui.button(
                        icon="arrow_forward",
                        on_click=lambda: self.move_widget_right(index),
                    ).props("round glossy")
                    ui.button(
                        icon="delete", on_click=lambda: self.remove_widget(index)
                    ).props("round glossy")
                    ui.button(
                        icon="settings",
                        on_click=lambda: self.edit_widget_configuration(index),
                    ).props("round glossy")

        with ui.card_section().classes("w-full h-full"):
            if widget:
                widget.create_widget(widget_info["widget_configuration"])

    def edit_widget_configuration(self, index):
        """Edit the widget configuration."""
        widget_info = self.page_widget_layout_configuration[index]
        widget = self.get_widget_by_id(
            widget_info["widget_id"],
            widget_info["widget_configuration"],
            widget_info["widget_instance_id"],
        )

        # Add width configuration
        def update_width(new_width):
            widget.widget_width = new_width
            self.render_widgets.refresh()

        with ui.row():
            ui.label("Widget Width:")
            ui.select(
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                value=widget.widget_width,
                on_change=lambda e: update_width(e.value),
            )

        widget.widget_configuration_form()

        self.set_page_mode("create")
        self.render_widgets.refresh()

    def move_widget_left(self, index):
        """Move the widget one position to the left in the configured_page_widgets array."""
        if index > 0:
            (
                self.page_widget_layout_configuration[index],
                self.page_widget_layout_configuration[index - 1],
            ) = (
                self.page_widget_layout_configuration[index - 1],
                self.page_widget_layout_configuration[index],
            )
            self.render_widgets.refresh()  # Refresh to update widget positions

    def move_widget_right(self, index):
        """Move the widget one position to the right in the configured_page_widgets array."""
        if index < len(self.page_widget_layout_configuration) - 1:
            (
                self.page_widget_layout_configuration[index],
                self.page_widget_layout_configuration[index + 1],
            ) = (
                self.page_widget_layout_configuration[index + 1],
                self.page_widget_layout_configuration[index],
            )
            self.render_widgets.refresh()  # Refresh to update widget positions

    def remove_widget(self, index):
        """Remove the widget from the configured_page_widgets array."""
        del self.page_widget_layout_configuration[index]
        self.render_widgets.refresh()  # Refresh to update widget positions

    def save_layout(self):
        """Saves the current layout configuration to DynamoDB."""
        try:
            # Update the width in the configuration before saving
            for widget_info in self.page_widget_layout_configuration:
                widget = self.get_widget_by_id(
                    widget_info["widget_id"],
                    widget_info["widget_configuration"],
                    widget_info["widget_instance_id"],
                )
                # Only update width if widget exists and has width attribute
                if widget and hasattr(widget, "widget_width"):
                    widget_info["widget_configuration"][
                        "widget_width"
                    ] = widget.widget_width
                else:
                    # Ensure there's a default width in the configuration
                    widget_info["widget_configuration"].setdefault("widget_width", 5)

            self.dynamo_table.update_item(
                Key={"uuid": self.cognito_adapter.get_user_id(), "tag": self.tag_name},
                UpdateExpression="SET configured_page_widgets = :widgets",
                ExpressionAttributeValues={
                    ":widgets": self.page_widget_layout_configuration
                },
            )
            ui.notify("Layout Saved Successfully")
            self.set_page_mode("view")
            self.render_widgets.refresh()
        except Exception as e:
            print(f"Error saving layout to DynamoDB: {e}")
            ui.notify(f"Error saving layout: {str(e)}", type="negative")

    def render(self):
        ui.add_head_html(
            """
            <style>
            header {
            left:240px !important;
            }
            aside {
                width: 240px !important;}
            .q-drawer--no-top-padding {
                width: 240px !important;
            }
            .q-page-container {
                padding-left: 240px !important;
            }
            main {
                background-color: #EEF4FA;
            }
            </style>
            """
        )
        if not self.page_widget_layout_configuration:
            self.page_widget_layout_configuration = (
                self.get_widget_layout_configuration()
            )
        if self.page_title:
            ui.page_title(self.page_title)
            self.render_toolbar()
            self.render_sidebar_navigation()
            self.render_widgets()
