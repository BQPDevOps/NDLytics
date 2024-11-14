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
        root_route=None,
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
        self.root_route = root_route

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
            f"background: linear-gradient(22deg, rgba(0,68,102,1) 0%, rgba(0,68,102,1) 30%, rgba(0,131,196,1) 86%, rgba(0,90,135,1) 93%, rgba(0,82,124,1) 100%); width: 240px !important;"
        ):
            with ui.column().classes("flex h-screen w-full"):
                with ui.row().classes("flex justify-start items-center w-full"):
                    with ui.row().classes(
                        "w-full flex justify-center items-center"
                    ).style(f"overflow:hidden;background-color: transparent;"):
                        ui.image(
                            "static/images/branding/ndlytics_logo_dark.svg"
                        ).classes("w-2/3").style("height:40px;")

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
                                    selected = (
                                        self.page_route == route
                                        or self.root_route == route
                                    )

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

    def calculate_layout(self, widgets, total_width=12):
        rows = []
        current_row = []
        current_width = 0

        for widget in widgets:
            widget_instance = self.get_widget_by_id(
                widget["widget_id"],
                widget["widget_configuration"],
                widget["widget_instance_id"],
            )
            widget_width = widget["widget_configuration"].get("widget_width", 6)
            if current_width + widget_width > total_width:
                rows.append(current_row)
                current_row = [widget]
                current_width = widget_width
            else:
                current_row.append(widget)
                current_width += widget_width

        if current_row:
            rows.append(current_row)

        return rows

    @ui.refreshable
    def render_widgets(self):
        """Renders widgets based on their specified widths."""
        if self.page_mode == "create":
            self.render_widget_creator()
            return

        if self.page_mode == "edit":
            with ui.row().classes("w-full justify-end"):
                ui.button("Add Widget", on_click=self.toggle_widget_create_mode)
                ui.button("Save Layout", on_click=lambda: self.save_layout())

        layout = self.calculate_layout(self.page_widget_layout_configuration)

        for row in layout:
            with ui.row().classes("w-full flex flex-nowrap -mx-2"):
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

                        widget_width = widget_info["widget_configuration"].get(
                            "widget_width", 6
                        )
                        percentage_width = math.floor((widget_width / 12) * 100)
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
            if widget.widget_width < 12:
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
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
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


# # shared/WidgetPage.py
# import uuid
# import math

# import boto3
# from nicegui import ui, app

# from utils.helpers import cognito_adapter, gateway_adapter, s3_storage_adapter
# from utils.lists import get_list
# from theme import ThemeManager

# from components.widgets import *
# from typing import Dict, List, Optional


# class WidgetPage:
#     def __init__(
#         self,
#         page_title: str,
#         page_route: str,
#         page_description: str,
#         tag_name: str,
#         storage_manager,
#         creator_presets,
#     ):
#         self.theme_manager = ThemeManager()
#         self.page_title = page_title
#         self.page_route = page_route
#         self.page_description = page_description
#         self.tag_name = tag_name
#         self.dynamo_db = None
#         self.dynamo_table = None
#         self.storage = storage_manager
#         self.cognito_adapter = cognito_adapter()
#         self.gateway_adapter = gateway_adapter(storage_manager)
#         self.s3_adapter = s3_storage_adapter(storage_manager)
#         self.page_widget_layout_configuration = []
#         self.page_mode = "view"
#         self.df_store = {}
#         self.creator_widget_preview = None
#         self.creator_step = 0
#         self.creator_presets = creator_presets
#         self.drag_source_index = None  # Store drag source index
#         self._permission_cache = {}  # Cache for permission checks

#         self.layout_widget_id = (
#             f'{self.page_title.lower().replace(" ", "_")}_page_config'
#         )

#         self.toolbar_items = {
#             "menu": {
#                 "icon": "menu",
#                 "color": "blue",
#                 "direction": "left",
#             },
#             "submenu": [
#                 {
#                     "icon": "o_logout",
#                     "color": "blue-5",
#                     "callback": lambda: self.cognito_adapter.signout(),
#                 },
#                 {
#                     "icon": "o_construction",
#                     "color": "green-5",
#                     "callback": lambda: self.toggle_edit_mode(),
#                 },
#             ],
#         }

#         self.navigation_items = get_list("page_routes")
#         self._onload()

#     def _onload(self):
#         self.dynamo_db = boto3.resource("dynamodb", region_name="us-east-1")
#         self.dynamo_table = self.dynamo_db.Table("NDA_Settings_Table")

#     def get_dataframe(self, file_key):
#         """Retrieve a DataFrame from the store or load it from S3."""
#         if file_key not in self.df_store:
#             self.df_store[file_key] = self.s3_adapter.read_csv_to_dataframe(
#                 bucket_name="nda-storage-v1", file_key=file_key
#             )
#         return self.df_store[file_key]

#     def get_widget_by_id(
#         self, widget_id, widget_configuration=None, widget_instance_id=None
#     ):
#         """
#         Instantiates the widget component by its ID.
#         Widgets are responsible for their own data fetching and rendering.
#         """
#         # Ensure widget_configuration is always a dictionary
#         widget_configuration = widget_configuration or {}

#         widget_map = {
#             "wgt_section_title": WGT_Section_Title,
#             "wgt_growth_metrics": WGT_Growth_Metrics,
#             "wgt_operator_performance_analysis": WGT_Operator_Performance_Analysis,
#             "wgt_yearly_collections_comparison": WGT_Yearly_Collections_Comparison,
#             "wgt_mtd_collections": WGT_MTD_Collections,
#             "wgt_prior_month_collections": WGT_Prior_Month_Collections,
#             "wgt_call_duration_analysis": WGT_Call_Duration_Analysis,
#             "wgt_call_outcome_analysis": WGT_Call_Outcome_Analysis,
#         }

#         widget_class = widget_map.get(widget_id)
#         if widget_class:
#             if widget_id == "wgt_section_title":
#                 return widget_class(widget_configuration, widget_instance_id)
#             else:
#                 return widget_class(
#                     self.get_dataframe, widget_configuration, widget_instance_id
#                 )
#         else:
#             print(f"Unknown widget ID: {widget_id}")
#             return None

#     def set_creator_widget_preview(self, widget_id: str):
#         self.creator_widget_preview = self.get_widget_by_id(widget_id)

#     def set_creator_step(self, step: int):
#         self.creator_step = step

#     def set_page_mode(self, mode: str):
#         self.page_mode = mode

#     def get_widget_layout_configuration(self):
#         try:
#             response = self.dynamo_table.get_item(
#                 Key={
#                     "uuid": self.cognito_adapter.get_user_id(),
#                     "tag": self.tag_name,
#                 }
#             )
#             item = response.get("Item")
#             if item and "configured_page_widgets" in item:
#                 self.page_widget_layout_configuration = item["configured_page_widgets"]
#                 return self.page_widget_layout_configuration
#             else:
#                 ui.notify("No page layout found for this user.")
#                 return []
#         except Exception as e:
#             print(f"Error fetching page layout: {e}")
#             return []

#     def check_permission(self, required_permissions):
#         """Cache permission checks to avoid repeated calls."""
#         cache_key = tuple(sorted(required_permissions))  # Make the list hashable
#         if cache_key not in self._permission_cache:
#             self._permission_cache[cache_key] = self.cognito_adapter.has_permission(
#                 required_permissions
#             )
#         return self._permission_cache[cache_key]

#     def render_sidebar_navigation(self):
#         with ui.left_drawer(top_corner=True, bottom_corner=True).style(
#             f"background: linear-gradient(22deg, rgba(0,68,102,1) 0%, rgba(0,68,102,1) 30%, rgba(0,131,196,1) 86%, rgba(0,90,135,1) 93%, rgba(0,82,124,1) 100%); width: 240px !important;"
#         ):
#             with ui.column().classes("flex h-screen w-full"):
#                 with ui.row().classes("flex justify-start items-center w-full"):
#                     with ui.row().classes(
#                         "w-full flex justify-center items-center"
#                     ).style(
#                         f"overflow:hidden;background-color: transparent;"
#                         # f"overflow:hidden;background-color: white; border: 1px solid white; border-radius: 8px;"
#                     ):
#                         ui.image(
#                             "static/images/branding/ndlytics_logo_dark.svg"
#                             # "static/images/branding/ndlytics_logo_light.svg"
#                         ).classes("w-2/3").style("height:40px;")
#                     # with ui.row().classes("flex justify-center items-center w-full"):
#                     #     DateTimeDisplay()
#                     with ui.row().classes("flex justify-start items-center w-full"):
#                         with ui.list().props("bordered separator").classes(
#                             "w-full rounded-lg"
#                         ):
#                             for index, section in enumerate(self.navigation_items):
#                                 page_name = section["page_name"]
#                                 route = section["route"]
#                                 icon = section["icon"]
#                                 required_permissions = section.get(
#                                     "required_permissions", []
#                                 )

#                                 if not required_permissions or self.check_permission(
#                                     required_permissions
#                                 ):
#                                     selected = self.page_route == route

#                                     bg_color = (
#                                         f"{self.theme_manager.colors['primary']['highlight']}"
#                                         if selected
#                                         else f"{self.theme_manager.colors['secondary']['base']}"
#                                     )
#                                     box_shadow = (
#                                         "inset 0 0 10px rgba(255, 255, 255, 0.3)"
#                                         if selected
#                                         else ""
#                                     )

#                                     # Determine border radius based on visible items
#                                     if index == 0:
#                                         border_radius = "10px 10px 0 0"
#                                     elif index == len(self.navigation_items) - 1:
#                                         border_radius = "0 0 10px 10px"
#                                     else:
#                                         border_radius = "0"

#                                     with ui.item(
#                                         on_click=lambda p=route: ui.navigate.to(p)
#                                     ).style(
#                                         f"background-color: {bg_color}; color: white; box-shadow: {box_shadow}; border-radius: {border_radius};"
#                                     ):
#                                         with ui.item_section():
#                                             ui.icon(icon)
#                                         with ui.item_section():
#                                             ui.item_label(page_name).style(
#                                                 f"color: {self.theme_manager.colors['text']['base']}"
#                                             )
#                                 else:
#                                     # Debugging: Permission denied for this section
#                                     print(f"Permission denied for section: {page_name}")

#     def render_toolbar(self):
#         primary_menu = self.toolbar_items.get("menu")
#         secondary_menu = self.toolbar_items.get("submenu")

#         with ui.header().style("background-color:#EEF4FA"):
#             with ui.row().classes("flex w-full"):
#                 ui.space()
#                 with ui.element("q-fab").props(
#                     f"icon={primary_menu['icon']} color={primary_menu['color']} direction={primary_menu['direction']}"
#                 ):
#                     for item in secondary_menu:
#                         ui.element("q-fab-action").props(
#                             f"icon={item['icon']} color={item['color']}"
#                         ).on("click", item["callback"])
#             ui.separator()

#     def toggle_edit_mode(self):
#         """Toggle between edit and display modes."""
#         if self.page_mode == "edit":
#             self.set_page_mode("view")
#         else:
#             self.set_page_mode("edit")
#         self.render_widgets.refresh()

#     def toggle_widget_create_mode(self):
#         """Toggle widget create mode."""
#         self.set_page_mode("create")
#         self.render_widgets.refresh()

#     @ui.refreshable
#     def render_widget_creator_preview(self):
#         """Renders the widget creator with the updated configuration."""
#         if self.creator_widget_preview:
#             self.creator_widget_preview.create_widget()
#         else:
#             ui.label("No widget selected for preview.")

#     def handle_preset_widget_selection(self, widget_id):
#         """Handles the selection of a preset widget."""
#         self.creator_widget_preview = self.get_widget_by_id(widget_id)
#         if self.creator_widget_preview:
#             self.render_widget_creator.refresh()

#     @ui.refreshable
#     def render_configuration_step(self):
#         """Renders the widget configuration step."""
#         if self.creator_widget_preview:
#             self.creator_widget_preview.widget_configuration_form()
#         else:
#             ui.label("No widget selected for configuration.")

#     @ui.refreshable
#     def render_widget_creator(self):
#         with ui.row().style("display:flex;flex:1;height:85vh;width:100%"):
#             with ui.column().style(
#                 "display:flex;flex:2;width:50%;height:85vh;justify-content:center;align-items:center"
#             ):
#                 self.render_widget_creator_preview()

#             # Right column for widget selection and configuration
#             with ui.column().style("display:flex;flex:1;width:50%;height:85vh"):
#                 with ui.stepper().props("horizontal").classes(
#                     "w-full h-full"
#                 ) as stepper:
#                     # Step 1: Select Widget
#                     with ui.step("Select Widget"):
#                         with ui.scroll_area().style("width:100%;height:100%"):
#                             with ui.list().props("bordered separator").style(
#                                 "width:100%"
#                             ):
#                                 for widget in self.creator_presets:
#                                     widget_instance = self.get_widget_by_id(
#                                         widget["widget_id"]
#                                     )
#                                     widget_details = (
#                                         widget_instance.get_widget_details()
#                                     )
#                                     with ui.item():
#                                         with ui.item_section().style(
#                                             "display:flex;flex-direction:column;justify-content:center;"
#                                         ):
#                                             ui.item_label(
#                                                 widget_details["widget_name"]
#                                             ).classes("text-lg font-bold")
#                                             ui.item_label(
#                                                 widget_details["widget_description"]
#                                             ).props("caption")
#                                         ui.space()
#                                         with ui.item_section().style(
#                                             "display:flex;justify-content:center;align-items:flex-end"
#                                         ):
#                                             ui.button(
#                                                 "Select",
#                                                 on_click=lambda w=widget[
#                                                     "widget_id"
#                                                 ]: self.handle_preset_widget_selection(
#                                                     w
#                                                 ),
#                                             ).style("width:30%;text-align:right")

#                         with ui.column().style(
#                             "flex-direction:row;display:flex;width:100%;align-items:flex-end"
#                         ):
#                             ui.button("Cancel", on_click=self.toggle_edit_mode)
#                             ui.space()
#                             with ui.stepper_navigation():
#                                 ui.button("Next").on("click", stepper.next)

#                     # Step 2: Configure Widget
#                     with ui.step("Configure Widget"):
#                         if self.creator_widget_preview:
#                             self.creator_widget_preview.widget_configuration_form()
#                         else:
#                             ui.label("No widget selected for configuration.")
#                         with ui.stepper_navigation().style(
#                             "display:flex;height:100%;width:100%"
#                         ):
#                             with ui.row().classes(
#                                 "w-full h-full justify-between items-end"
#                             ):
#                                 ui.button("Back").on("click", stepper.previous)
#                                 ui.button(
#                                     "Finish",
#                                     on_click=(lambda: self.add_widget_to_layout()),
#                                 )

#     def add_widget_to_layout(self):
#         """Add the widget to the user's layout preferences."""
#         if self.creator_widget_preview:
#             widget = self.creator_widget_preview.get_widget_details()
#             if widget["widget_instance_id"] is None:
#                 ui.notify("Adding widget to layout...")
#                 widget["widget_instance_id"] = self.generate_widget_id()
#                 widget["widget_width"] = 5  # Default to half width
#                 self.page_widget_layout_configuration.append(widget)
#             else:
#                 self.update_configured_page_layout(
#                     widget["widget_instance_id"],
#                     "widget_configuration",
#                     widget["widget_configuration"],
#                 )
#             self.set_page_mode("edit")
#         else:
#             ui.notify("No widget selected for addition.")
#         self.render_widgets.refresh()

#     def update_configured_page_layout(self, widget_instance_id, key, value):
#         widget_list = self.page_widget_layout_configuration
#         for widget in widget_list:
#             if widget.get("widget_instance_id") == widget_instance_id:
#                 widget[key] = value
#                 break  # Exit the loop once the widget is found and updated
#         self.page_widget_layout_configuration = widget_list

#     def generate_widget_id(self):
#         """Generates a random widget_id to avoid duplicates."""
#         return str(uuid.uuid4())  # Use UUID to generate unique IDs

#     def calculate_layout(self, widgets, total_width=12):
#         """Calculate layout with two columns per row and width constraints."""
#         rows = []
#         current_row = []
#         current_width = 0.0

#         for widget in widgets:
#             widget_width = float(widget["widget_configuration"].get("widget_width", 6))

#             # Check if adding this widget would exceed row width or max widgets per row
#             if len(current_row) == 2 or (current_width + widget_width > total_width):
#                 rows.append(current_row)
#                 current_row = [widget]
#                 current_width = widget_width
#             else:
#                 current_row.append(widget)
#                 current_width += widget_width

#         # Add the last row if it has any widgets
#         if current_row:
#             rows.append(current_row)

#         return rows

#     def swap_widgets(self, source_index: int, target_index: int) -> None:
#         """Swap two widgets in the configuration."""
#         if source_index != target_index:
#             widgets = self.page_widget_layout_configuration
#             # Store the widgets to swap
#             source_widget = widgets[source_index]
#             target_widget = widgets[target_index]

#             # Perform the swap
#             widgets[source_index] = target_widget
#             widgets[target_index] = source_widget

#             # Update the configuration
#             self.page_widget_layout_configuration = widgets
#             self.render_widgets.refresh()

#     class WidgetContainer(ui.column):
#         def __init__(self, parent_page, row_index: int) -> None:
#             super().__init__()
#             self.parent_page = parent_page
#             self.row_index = row_index

#             # Create two columns per row
#             with self.classes("w-full p-4 flex gap-4"):
#                 # Left column (first widget slot)
#                 self.left_container = ui.element("div").classes(
#                     "drop-column left-column"
#                 )
#                 with self.left_container:
#                     self.left_column = ui.element("div").classes("column-content")

#                 # Right column (second widget slot)
#                 self.right_container = ui.element("div").classes(
#                     "drop-column right-column"
#                 )
#                 with self.right_container:
#                     self.right_column = ui.element("div").classes("column-content")

#             self.on("dragover.prevent", self.highlight)
#             self.on("dragleave", self.unhighlight)
#             self.on("drop", self.handle_drop)

#         def set_column_width(self, column: str, width: float) -> None:
#             """Set the width of a column container based on the 12-column grid."""
#             percentage_width = math.floor((width / 12) * 100)
#             if column == "left":
#                 self.left_container.style(f"width: {percentage_width}%")
#             else:
#                 self.right_container.style(f"width: {percentage_width}%")

#         def highlight(self) -> None:
#             self.classes(add="row-highlight")

#         def unhighlight(self) -> None:
#             self.classes(remove="row-highlight")

#         def handle_drop(self) -> None:
#             global dragged_widget
#             self.unhighlight()

#             if dragged_widget:
#                 old_index = self.parent_page.page_widget_layout_configuration.index(
#                     dragged_widget.widget_info
#                 )
#                 new_index = self.row_index * 2

#                 # Remove from old position
#                 self.parent_page.page_widget_layout_configuration.pop(old_index)

#                 # Insert at new position
#                 if new_index >= len(self.parent_page.page_widget_layout_configuration):
#                     self.parent_page.page_widget_layout_configuration.append(
#                         dragged_widget.widget_info
#                     )
#                 else:
#                     self.parent_page.page_widget_layout_configuration.insert(
#                         new_index, dragged_widget.widget_info
#                     )

#                 self.parent_page.render_widgets.refresh()
#                 dragged_widget = None

#     class DraggableWidget(ui.card):
#         def __init__(self, parent_page, widget_info: dict, index: int) -> None:
#             super().__init__()
#             self.parent_page = parent_page
#             self.widget_info = widget_info
#             self.index = index

#             with self.props("draggable").classes("widget-card w-full cursor-move"):
#                 self.render_widget_content()

#             # Add all drag events
#             self.on("dragstart", self.handle_dragstart)
#             self.on("dragover.prevent", self.handle_dragover)
#             self.on("drop", self.handle_drop)
#             self.on("dragend", self.handle_dragend)

#         def handle_dragstart(self) -> None:
#             global dragged_widget
#             dragged_widget = self
#             self.classes(add="dragging")

#         def handle_dragover(self) -> None:
#             if dragged_widget and dragged_widget != self:
#                 self.classes(add="drag-over")

#         def handle_drop(self) -> None:
#             if dragged_widget and dragged_widget != self:
#                 # Get indices
#                 source_index = dragged_widget.index
#                 target_index = self.index

#                 # Swap widgets in the configuration
#                 self.parent_page.swap_widgets(source_index, target_index)
#                 self.classes(remove="drag-over")

#         def handle_dragend(self) -> None:
#             self.classes(remove="dragging")
#             # Fix the query iteration issue
#             drag_over_elements = ui.query(".drag-over").classes()
#             if drag_over_elements:
#                 for class_name in drag_over_elements:
#                     if "drag-over" in class_name:
#                         ui.query(f".{class_name}").remove_class("drag-over")

#         def render_widget_content(self) -> None:
#             widget = self.parent_page.get_widget_by_id(
#                 self.widget_info["widget_id"],
#                 self.widget_info["widget_configuration"],
#                 self.widget_info["widget_instance_id"],
#             )

#             with ui.row().classes("w-full justify-between items-center"):
#                 with ui.row().classes("items-center gap-2"):
#                     ui.icon("drag_indicator").classes("drag-handle")
#                     ui.label(f"Width: {widget.widget_width}").classes("text-body1")
#                     ui.number(
#                         value=widget.widget_width,
#                         min=1,
#                         max=12,
#                         step=1,
#                         on_change=lambda e: self.parent_page.update_widget_width(
#                             self.index, e.value
#                         ),
#                     )

#                 with ui.row():
#                     ui.button(
#                         icon="delete",
#                         on_click=lambda: self.parent_page.remove_widget(self.index),
#                     ).props("round glossy")
#                     ui.button(
#                         icon="settings",
#                         on_click=lambda: self.parent_page.edit_widget_configuration(
#                             self.index
#                         ),
#                     ).props("round glossy")

#             with ui.card_section().classes("w-full h-full"):
#                 widget.create_widget(self.widget_info["widget_configuration"])

#     @ui.refreshable
#     def render_widgets(self):
#         """Renders widgets in a two-column layout."""
#         if self.page_mode == "create":
#             self.render_widget_creator()
#             return

#         if self.page_mode == "edit":
#             with ui.row().classes("w-full justify-end"):
#                 ui.button("Add Widget", on_click=self.toggle_widget_create_mode)
#                 ui.button("Save Layout", on_click=lambda: self.save_layout())

#         # Main container for all rows
#         with ui.element("div").classes("widgets-container"):
#             layout = self.calculate_layout(self.page_widget_layout_configuration)

#             # Create containers for each row
#             for row_index, row in enumerate(layout):
#                 # Row container
#                 with ui.element("div").classes("widget-row"):
#                     # Calculate total width used in this row
#                     used_width = sum(
#                         float(w["widget_configuration"].get("widget_width", 6))
#                         for w in row
#                     )
#                     remaining_width = 12 - used_width

#                     # Render widgets in the row
#                     for col_index, widget_info in enumerate(row):
#                         widget_width = float(
#                             widget_info["widget_configuration"].get("widget_width", 6)
#                         )
#                         percentage_width = math.floor((widget_width / 12) * 100)

#                         # Widget container
#                         with ui.element("div").classes("widget-column").style(
#                             f"width: {percentage_width}%;"
#                         ):
#                             if self.page_mode == "edit":
#                                 self.DraggableWidget(
#                                     self, widget_info, row_index * 2 + col_index
#                                 )
#                             else:
#                                 self.render_widget_display_mode(widget_info)

#                     # Add empty column if there's only one widget
#                     if len(row) == 1 and remaining_width > 0:
#                         empty_percentage = math.floor((remaining_width / 12) * 100)
#                         with ui.element("div").classes(
#                             "widget-column empty-column"
#                         ).style(f"width: {empty_percentage}%;"):
#                             ui.label("Drop Widget Here").classes("empty-column-text")

#     def render_widget_display_mode(self, widget_info):
#         """Renders the widget in display mode."""
#         widget = self.get_widget_by_id(
#             widget_info["widget_id"],
#             widget_info["widget_configuration"],
#             widget_info["widget_instance_id"],
#         )
#         if widget:
#             with ui.card_section().classes("w-full h-full"):
#                 widget.create_widget(widget_info["widget_configuration"])
#         else:
#             print(f"Skipping widget with ID: {widget_info['widget_id']}")

#     def render_widget_edit_mode_draggable(self, index, widget_info):
#         """Renders the widget with edit controls and drag handle."""
#         widget = self.get_widget_by_id(
#             widget_info["widget_id"],
#             widget_info["widget_configuration"],
#             widget_info["widget_instance_id"],
#         )

#         with ui.card().classes("widget-card").props(f'data-widget-index="{index}"'):
#             with ui.row().classes("w-full justify-between items-center"):
#                 with ui.row().classes("items-center gap-2"):
#                     ui.icon("drag_indicator").classes("drag-handle")
#                     ui.label(f"Width: {widget.widget_width}").classes("text-body1")
#                     ui.number(
#                         value=widget.widget_width,
#                         min=1,
#                         max=12,
#                         step=1,
#                         on_change=lambda e: self.update_widget_width(index, e.value),
#                     )

#                 with ui.row():
#                     ui.button(
#                         icon="delete", on_click=lambda: self.remove_widget(index)
#                     ).props("round glossy")
#                     ui.button(
#                         icon="settings",
#                         on_click=lambda: self.edit_widget_configuration(index),
#                     ).props("round glossy")

#             with ui.card_section().classes("w-full h-full"):
#                 if widget:
#                     widget.create_widget(widget_info["widget_configuration"])

#     def edit_widget_configuration(self, index):
#         """Edit the widget configuration."""
#         widget_info = self.page_widget_layout_configuration[index]
#         widget = self.get_widget_by_id(
#             widget_info["widget_id"],
#             widget_info["widget_configuration"],
#             widget_info["widget_instance_id"],
#         )

#         # Add width configuration
#         def update_width(new_width):
#             widget.widget_width = new_width
#             self.render_widgets.refresh()

#         with ui.row():
#             ui.label("Widget Width:")
#             ui.select(
#                 [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
#                 value=widget.widget_width,
#                 on_change=lambda e: update_width(e.value),
#             )

#         widget.widget_configuration_form()

#         self.set_page_mode("create")
#         self.render_widgets.refresh()

#     def move_widget_left(self, index):
#         """Move the widget one position to the left in the configured_page_widgets array."""
#         if index > 0:
#             (
#                 self.page_widget_layout_configuration[index],
#                 self.page_widget_layout_configuration[index - 1],
#             ) = (
#                 self.page_widget_layout_configuration[index - 1],
#                 self.page_widget_layout_configuration[index],
#             )
#             self.render_widgets.refresh()  # Refresh to update widget positions

#     def move_widget_right(self, index):
#         """Move the widget one position to the right in the configured_page_widgets array."""
#         if index < len(self.page_widget_layout_configuration) - 1:
#             (
#                 self.page_widget_layout_configuration[index],
#                 self.page_widget_layout_configuration[index + 1],
#             ) = (
#                 self.page_widget_layout_configuration[index + 1],
#                 self.page_widget_layout_configuration[index],
#             )
#             self.render_widgets.refresh()  # Refresh to update widget positions

#     def remove_widget(self, index):
#         """Remove the widget from the configured_page_widgets array."""
#         del self.page_widget_layout_configuration[index]
#         self.render_widgets.refresh()  # Refresh to update widget positions

#     def save_layout(self):
#         """Saves the current layout configuration to DynamoDB."""
#         try:
#             # Update the width in the configuration before saving
#             for widget_info in self.page_widget_layout_configuration:
#                 widget = self.get_widget_by_id(
#                     widget_info["widget_id"],
#                     widget_info["widget_configuration"],
#                     widget_info["widget_instance_id"],
#                 )
#                 # Only update width if widget exists and has width attribute
#                 if widget and hasattr(widget, "widget_width"):
#                     widget_info["widget_configuration"][
#                         "widget_width"
#                     ] = widget.widget_width
#                 else:
#                     # Ensure there's a default width in the configuration
#                     widget_info["widget_configuration"].setdefault("widget_width", 5)

#             self.dynamo_table.update_item(
#                 Key={"uuid": self.cognito_adapter.get_user_id(), "tag": self.tag_name},
#                 UpdateExpression="SET configured_page_widgets = :widgets",
#                 ExpressionAttributeValues={
#                     ":widgets": self.page_widget_layout_configuration
#                 },
#             )
#             ui.notify("Layout Saved Successfully")
#             self.set_page_mode("view")
#             self.render_widgets.refresh()
#         except Exception as e:
#             print(f"Error saving layout to DynamoDB: {e}")
#             ui.notify(f"Error saving layout: {str(e)}", type="negative")

#     def handle_drag_start(self, index: int) -> None:
#         """Store the source index and widget when drag starts."""
#         self.drag_source_index = index
#         # Store the dragged widget info
#         self.dragged_widget = self.page_widget_layout_configuration[index]

#     def handle_drag_end(self, target_index: int) -> None:
#         """Handle the drop event and reorder widgets with layout consideration."""
#         if (
#             self.drag_source_index is not None
#             and self.drag_source_index != target_index
#         ):
#             # Remove widget from source position
#             widget = self.page_widget_layout_configuration.pop(self.drag_source_index)

#             # Calculate target position considering layout
#             layout = self.calculate_layout(self.page_widget_layout_configuration)
#             flat_layout = [item for row in layout for item in row]

#             # Insert at target position
#             if target_index >= len(self.page_widget_layout_configuration):
#                 self.page_widget_layout_configuration.append(widget)
#             else:
#                 self.page_widget_layout_configuration.insert(target_index, widget)

#             # Reset drag state
#             self.drag_source_index = None
#             self.dragged_widget = None

#             # Recalculate layout and refresh
#             self.render_widgets.refresh()

#     def handle_widget_reorder(self, new_order: List[str]) -> None:
#         """Handle widget reordering from dragula."""
#         new_configuration = []
#         for index in new_order:
#             widget = self.page_widget_layout_configuration[int(index)]
#             new_configuration.append(widget)
#         self.page_widget_layout_configuration = new_configuration
#         self.render_widgets.refresh()

#     def update_widget_width(self, index: int, new_width: int) -> None:
#         """Update the width of a widget."""
#         try:
#             # Convert new_width to float before storing
#             new_width_float = float(new_width)
#             self.page_widget_layout_configuration[index]["widget_configuration"][
#                 "widget_width"
#             ] = new_width_float
#             self.render_widgets.refresh()
#         except (ValueError, TypeError) as e:
#             print(f"Error updating widget width: {e}")
#             ui.notify("Error updating widget width", type="negative")

#     def render(self):
#         ui.add_head_html(
#             """
#             <style>
#                 .widgets-container {
#                     display: flex;
#                     flex-direction: column;
#                     gap: 1rem;
#                     width: 100%;
#                     padding: 1rem;
#                 }

#                 .widget-row {
#                     display: flex;
#                     flex-direction: row;
#                     gap: 1rem;
#                     width: 100%;
#                     min-height: 100px;
#                 }

#                 .widget-column {
#                     display: flex;
#                     flex-direction: column;
#                     min-height: 100px;
#                     background-color: rgba(0,0,0,0.02);
#                     border-radius: 8px;
#                     transition: all 0.3s ease;
#                     padding: 1rem;
#                 }

#                 .widget-card {
#                     width: 100%;
#                     height: 100%;
#                     opacity: 1;
#                     transition: all 0.3s ease;
#                     position: relative;
#                 }

#                 .widget-card[draggable="true"] {
#                     cursor: move;
#                 }

#                 .widget-card.dragging {
#                     opacity: 0.5;
#                     box-shadow: 0 8px 16px rgba(0,0,0,0.2);
#                     z-index: 1000;
#                 }

#                 .widget-card.drag-over {
#                     transform: scale(1.02);
#                     box-shadow: 0 0 20px rgba(0,102,204,0.2);
#                     border: 2px dashed #0066cc;
#                 }

#                 .drag-handle {
#                     cursor: move;
#                     user-select: none;
#                 }

#                 .empty-column {
#                     border: 2px dashed rgba(0,0,0,0.1);
#                     background-color: rgba(0,0,0,0.03);
#                     display: flex;
#                     align-items: center;
#                     justify-content: center;
#                 }

#                 .empty-column-text {
#                     color: rgba(0,0,0,0.3);
#                     font-size: 0.9rem;
#                 }
#             </style>
#             """
#         )
#         if not self.page_widget_layout_configuration:
#             self.page_widget_layout_configuration = (
#                 self.get_widget_layout_configuration()
#             )
#         if self.page_title:
#             ui.page_title(self.page_title)
#             self.render_toolbar()
#             self.render_sidebar_navigation()
#             self.render_widgets()
