from nicegui import ui
from uuid import uuid4
import arrow
import botocore.exceptions

from config import config
from utils.helpers import dynamo_adapter
from components.shared import StaticPage
from models import ManagedState

from typing import List


class TicketSchema:
    def __init__(
        self,
        uuid: str,
        category: str,
        description: str,
        required_permissions: List[str],
    ):
        self.uuid = uuid
        self.category = category
        self.description = description
        self.required_permissions = required_permissions
        self.subcategories: List[TicketSubCategory] = []  # Initialize empty list


class TicketSubCategory:
    def __init__(
        self, uuid: str, subcategory: str, description: str, status_options: List[str]
    ):
        self.uuid = uuid
        self.subcategory = subcategory
        self.description = description
        self.status_options = status_options


class SettingsTicketSystem(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Ticket System Settings",
            page_route="/settings/ticket-system",
            page_description="Ticket System Settings",
            storage_manager=storage_manager,
        )
        self.dynamo_adapter = dynamo_adapter(config.aws_settings_table_name)
        self.state = ManagedState("ticket_system_settings")
        self.state.set("schemas", [])
        self.state.set("active_view", "default_view")
        self.state.set("category_view", "empty_view")
        self.state.set("subcategory_view", "empty_view")
        self.state.set("settings_view", "empty_view")
        self.state.set("selected_category", None)
        self.state.set("selected_subcategory", None)
        self.state.set("selected_description", None)
        self.state.set("selected_settings", {})
        self._load_ticket_system_settings()

    def _load_ticket_system_settings(self):
        try:
            response = self.dynamo_adapter.get_item(
                {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}
            )
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ValidationException":
                default_record = {
                    "uuid": {"S": "ticket_system"},
                    "tag": {"S": "ticket_system_schemas"},
                    "ticket_schemas": {"L": []},  # Empty list of schemas
                }
                self.dynamo_adapter.put_item(default_record)
                return []
            else:
                raise e

        if not response:
            return []

        # Extract the list of ticket schemas from the DynamoDB response
        ticket_data_list = response.get("ticket_schemas", {"L": []})["L"]

        schema_list = []
        for ticket_data in ticket_data_list:
            ticket_map = ticket_data["M"]

            # Create TicketSchema instance
            schema = TicketSchema(
                uuid=ticket_map["uuid"]["S"],
                category=ticket_map["category"]["S"],
                description=ticket_map["description"]["S"],
                required_permissions=[
                    p["S"] for p in ticket_map["required_permissions"]["L"]
                ],
            )

            # Add subcategories
            for sub_data in ticket_map.get("subcategories", {"L": []})["L"]:
                sub_map = sub_data["M"]
                subcategory = TicketSubCategory(
                    uuid=sub_map["uuid"]["S"],
                    subcategory=sub_map["subcategory"]["S"],
                    description=sub_map["description"]["S"],
                    status_options=[s["S"] for s in sub_map["status_options"]["L"]],
                )
                schema.subcategories.append(subcategory)

            schema_list.append(schema)

        print(schema_list)
        self.state.set("schemas", schema_list)
        self.state.set("category_view", "display_list_view")

    def _save_ticket_system_settings(self):
        schemas = self.state.get("schemas")
        schema_list = []

        for schema in schemas:
            subcategories_list = []
            for sub in schema.subcategories:
                subcategories_list.append(
                    {
                        "M": {
                            "uuid": {"S": sub.uuid},
                            "subcategory": {"S": sub.subcategory},
                            "description": {"S": sub.description},
                            "status_options": {
                                "L": [{"S": status} for status in sub.status_options]
                            },
                        }
                    }
                )

            schema_dict = {
                "M": {
                    "uuid": {"S": schema.uuid},
                    "category": {"S": schema.category},
                    "description": {"S": schema.description},
                    "required_permissions": {
                        "L": [{"S": perm} for perm in schema.required_permissions]
                    },
                    "subcategories": {"L": subcategories_list},
                }
            }
            schema_list.append(schema_dict)

        item = {
            "uuid": {"S": "ticket_system"},
            "tag": {"S": "ticket_system_schemas"},
            "ticket_schemas": {"L": schema_list},
        }
        self.dynamo_adapter.put_item(item)

    @ui.refreshable
    def transition_content_view(self):
        render_view = self.state.get("active_view")
        view_map = {
            "default_view": self._default_view,
        }
        render_function = view_map.get(render_view, "default_view")
        render_function()

    # Category View Methods
    @ui.refreshable
    def transition_category_view(self):
        render_view = self.state.get("category_view")
        view_map = {
            "empty_view": self._category_empty_view,
            "display_list_view": self._category_display_list_view,
        }
        render_function = view_map.get(render_view, "empty_view")
        render_function()

    def _category_empty_view(self):
        with ui.column().classes("w-full h-full items-center justify-center"):
            ui.label("No categories available").classes("text-lg text-gray-500")

    def _category_display_list_view(self):
        schemas = self.state.get("schemas")

        if not schemas:
            with ui.column().classes("w-full h-full items-center justify-center"):
                ui.label("No categories available").classes("text-lg text-gray-500")
                return

        with ui.column().classes("w-full gap-2 p-4"):
            # Display each category as a card
            for schema in schemas:
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-100").on(
                    "click", lambda s=schema: self._select_category(s)
                ):
                    with ui.row().classes("w-full items-center justify-between p-2"):
                        with ui.column().classes("gap-1 flex-grow"):
                            ui.label(schema.category).classes("text-lg font-bold")
                            ui.label(schema.description).classes(
                                "text-sm text-gray-600"
                            )
                            ui.label(
                                f"Subcategories: {len(schema.subcategories)}"
                            ).classes("text-xs text-gray-500")
                        with ui.row().classes("gap-2 ml-2"):
                            ui.button(
                                icon="edit",
                                on_click=lambda s=schema: self._show_category_dialog(s),
                            ).props("flat").classes("min-w-0")
                            ui.button(
                                icon="delete",
                                on_click=lambda s=schema: self._delete_category(s),
                            ).props("flat color=negative").classes("min-w-0")

    def _show_category_dialog(self, schema=None):
        is_edit = schema is not None
        with ui.dialog() as dialog, ui.card().classes("p-4 w-96"):
            ui.label("Add Category" if not is_edit else "Edit Category").classes(
                "text-xl font-bold mb-4"
            )
            category = ui.input(
                "Category Name", value=schema.category if is_edit else ""
            ).classes("w-full")
            description = ui.input(
                "Description", value=schema.description if is_edit else ""
            ).classes("w-full")
            permissions = ui.input(
                "Required Permissions (comma-separated)",
                value=",".join(schema.required_permissions) if is_edit else "",
            ).classes("w-full")

            def save():
                perms = [p.strip() for p in permissions.value.split(",") if p.strip()]
                if is_edit:
                    schema.category = category.value
                    schema.description = description.value
                    schema.required_permissions = perms
                else:
                    new_schema = TicketSchema(
                        uuid=str(uuid4()),
                        category=category.value,
                        description=description.value,
                        required_permissions=perms,
                    )
                    schemas = self.state.get("schemas")
                    schemas.append(new_schema)
                    self.state.set("schemas", schemas)

                self._save_ticket_system_settings()
                self.transition_category_view.refresh()
                dialog.close()

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close)
                ui.button("Save", on_click=save).props("color=primary")

    def _select_category(self, schema):
        self.state.set("selected_category", schema)
        self.state.set("subcategory_view", "display_list_view")
        self.transition_subcategory_view.refresh()

    def _delete_category(self, schema):
        def confirm_delete():
            schemas = self.state.get("schemas")
            schemas.remove(schema)
            self.state.set("schemas", schemas)
            self._save_ticket_system_settings()
            self.transition_category_view.refresh()
            dialog.close()

        with ui.dialog() as dialog, ui.card().classes("p-4"):
            ui.label(f"Delete category '{schema.category}'?").classes("text-lg mb-4")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close)
                ui.button("Delete", on_click=confirm_delete).props("color=negative")

    # Subcategory View Methods
    @ui.refreshable
    def transition_subcategory_view(self):
        render_view = self.state.get("subcategory_view")
        view_map = {
            "empty_view": self._subcategory_empty_view,
            "display_list_view": self._subcategory_display_list_view,
        }
        render_function = view_map.get(render_view, "empty_view")
        render_function()

    def _subcategory_empty_view(self):
        with ui.column().classes("w-full h-full items-center justify-center"):
            ui.label("Select a category to view subcategories").classes(
                "text-lg text-gray-500"
            )

    def _subcategory_display_list_view(self):
        selected_category = self.state.get("selected_category")
        if not selected_category:
            return self._subcategory_empty_view()

        with ui.column().classes("w-full gap-2 p-4"):
            for subcategory in selected_category.subcategories:
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-100").on(
                    "click", lambda s=subcategory: self._select_subcategory(s)
                ):
                    with ui.row().classes("w-full items-center justify-between p-2"):
                        with ui.column().classes("gap-1"):
                            ui.label(subcategory.subcategory).classes(
                                "text-lg font-bold"
                            )
                            ui.label(subcategory.description).classes(
                                "text-sm text-gray-600"
                            )
                        with ui.row().classes("gap-2"):
                            ui.button(
                                icon="edit",
                                on_click=lambda s=subcategory: self._show_subcategory_dialog(
                                    selected_category, s
                                ),
                            )
                            ui.button(
                                icon="delete",
                                on_click=lambda s=subcategory: self._delete_subcategory(
                                    selected_category, s
                                ),
                            )

    def _show_subcategory_dialog(self, category, subcategory=None):
        is_edit = subcategory is not None
        with ui.dialog() as dialog, ui.card().classes("p-4 w-96"):
            ui.label("Add Subcategory" if not is_edit else "Edit Subcategory").classes(
                "text-xl font-bold mb-4"
            )
            name = ui.input(
                "Subcategory Name", value=subcategory.subcategory if is_edit else ""
            ).classes("w-full")
            description = ui.input(
                "Description", value=subcategory.description if is_edit else ""
            ).classes("w-full")

            # Status options management
            status_options = []
            with ui.column().classes("w-full gap-2"):
                ui.label("Status Options").classes("font-bold mt-4")

                def add_status_option(initial_value=""):
                    with ui.row().classes("w-full gap-2") as row:
                        input = ui.input("Status", value=initial_value).classes(
                            "flex-grow"
                        )
                        status_options.append(input)
                        ui.button(
                            icon="remove",
                            on_click=lambda: (
                                status_options.remove(input),
                                row.delete(),
                            ),
                        )

                # Add existing status options if editing
                if is_edit:
                    for status in subcategory.status_options:
                        add_status_option(status)

                ui.button(
                    "Add Status Option",
                    icon="add",
                    on_click=lambda: add_status_option(),
                )

            def save():
                status_values = [s.value for s in status_options if s.value.strip()]
                if is_edit:
                    subcategory.subcategory = name.value
                    subcategory.description = description.value
                    subcategory.status_options = status_values
                else:
                    new_subcategory = TicketSubCategory(
                        uuid=str(uuid4()),
                        subcategory=name.value,
                        description=description.value,
                        status_options=status_values,
                    )
                    category.subcategories.append(new_subcategory)

                self._save_ticket_system_settings()
                self.transition_subcategory_view.refresh()
                dialog.close()

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close)
                ui.button("Save", on_click=save).props("color=primary")

    def _select_subcategory(self, subcategory):
        self.state.set("selected_subcategory", subcategory)
        self.state.set("settings_view", "display_settings_view")
        self.transition_settings_view.refresh()

    def _delete_subcategory(self, category, subcategory):
        def confirm_delete():
            category.subcategories.remove(subcategory)
            self._save_ticket_system_settings()
            self.transition_subcategory_view.refresh()
            dialog.close()

        with ui.dialog() as dialog, ui.card().classes("p-4"):
            ui.label(f"Delete subcategory '{subcategory.subcategory}'?").classes(
                "text-lg mb-4"
            )
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close)
                ui.button("Delete", on_click=confirm_delete).props("color=negative")

    def _default_view(self):
        def custom_separator():
            with ui.column().classes("flex justify-center items-center h-[100%] w-fit"):
                with ui.card().tight().classes(
                    f"w-[3rem] h-[3rem] flex justify-center items-center rounded-full bg-[{self.theme_manager.get_color('button-basic')}]"
                ):
                    ui.icon("o_keyboard_arrow_right").classes("text-4xl text-white")

        def list_section(title: str, on_add=None, show_add=True):
            with ui.column().style("width:100%;display:flex;flex:1;height:100%;"):
                with ui.card().style("width:100%;height:100%;"):
                    with ui.row().classes(
                        "w-full justify-between items-center p-4 border-b"
                    ):
                        ui.label(title).classes("text-xl font-bold")
                        if show_add:
                            add_button = (
                                ui.button(icon="add").props("flat").classes("ml-2")
                            )
                            if on_add:
                                add_button.on("click", on_add)
                            return add_button
                    with ui.column().classes("flex-1 overflow-auto"):
                        return ui.column()

        with ui.row().style("display:flex;flex-direction:row;width:100%;height:80vh;"):
            # Categories Section
            list_container = list_section(
                "Categories", on_add=lambda: self._show_category_dialog()
            )
            with list_container:
                self.transition_category_view()

            custom_separator()

            # Subcategories Section
            list_container = list_section(
                "Subcategories",
                on_add=lambda: (
                    self._show_subcategory_dialog(self.state.get("selected_category"))
                    if self.state.get("selected_category")
                    else None
                ),
                show_add=self.state.get("selected_category") is not None,
            )
            with list_container:
                self.transition_subcategory_view()

            custom_separator()

            # Settings Section
            list_container = list_section("Settings", show_add=False)
            with list_container:
                self.transition_settings_view()

    def content(self):
        """Implementation of the abstract method from StaticPage"""
        with ui.column().classes("w-full h-full"):
            self.transition_content_view()

    # Settings View Methods
    @ui.refreshable
    def transition_settings_view(self):
        render_view = self.state.get("settings_view")
        view_map = {
            "empty_view": self._settings_empty_view,
            "display_settings_view": self._settings_display_view,
        }
        render_function = view_map.get(render_view, "empty_view")
        render_function()

    def _settings_empty_view(self):
        with ui.column().classes("w-full h-full items-center justify-center"):
            ui.label("Select a subcategory to view settings").classes(
                "text-lg text-gray-500"
            )

    def _settings_display_view(self):
        subcategory = self.state.get("selected_subcategory")
        if not subcategory:
            return self._settings_empty_view()

        with ui.column().classes("w-full gap-4 p-4"):
            ui.label("Subcategory Settings").classes("text-xl font-bold")

            with ui.card().classes("w-full p-4"):
                ui.label("Details").classes("text-lg font-bold mb-2")
                with ui.column().classes("gap-2"):
                    ui.label(f"Name: {subcategory.subcategory}")
                    ui.label(f"Description: {subcategory.description}")

            with ui.card().classes("w-full p-4"):
                ui.label("Status Options").classes("text-lg font-bold mb-2")
                with ui.column().classes("gap-2"):
                    for status in subcategory.status_options:
                        with ui.row().classes("w-full items-center"):
                            ui.label(status).classes("text-gray-700")


def ticket_system_settings_page(storage_manager):
    page = SettingsTicketSystem(storage_manager)
    page.render()
