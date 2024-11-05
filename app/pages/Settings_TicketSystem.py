from config import config
from utils.helpers import dynamo_adapter
from components.shared import StaticPage
from models import ManagedState

from nicegui import ui


class SettingsTicketSystem(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Ticket System Settings",
            page_route="/settings/ticket-system",
            page_description="Ticket System Settings",
            storage_manager=storage_manager,
        )
        self.state = ManagedState("ticket_system_settings")
        self.dynamo_adapter = dynamo_adapter(config.aws_settings_table_name)

        # Add CSS to prevent click propagation
        ui.add_head_html(
            """
            <style>
            .no-click {
                pointer-events: auto !important;
            }
            </style>
        """
        )

        self._get_schemas()

    def _get_schemas(self):
        """Retrieve ticket system schemas from DynamoDB and store in state"""
        key = {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}

        schema_data = self.dynamo_adapter.get_item(key)

        if schema_data:
            ticket_schemas = schema_data.get("schemas", [])
            ticket_categories = [
                schema.get("category", "") for schema in ticket_schemas
            ]
            self.state.set("ticket_schema", ticket_schemas)
            self.state.set("ticket_categories", ticket_categories)
        else:
            self.state.set("ticket_schema", [])
            self.state.set("ticket_categories", [])

        self.state.set("ticket_subcategories", [])

    def _get_subcategories(self, category):
        """Get subcategories for a specific category from the schema"""
        self.state.set("status_options", [])
        for schema in self.state.get("ticket_schema", []):
            if schema.get("category") == category:
                # Extract subcategories from the schema's subcategories list
                return [
                    sub.get("subcategory", "")
                    for sub in schema.get("subcategories", [])
                ]
        return []

    def _get_status_options(self, category):
        """Get status options for a specific category from the schema"""
        for schema in self.state.get("ticket_schema", []):
            if schema.get("category") == category:
                # Return both status and description for each status option
                return [
                    {
                        "status": status.get("status", ""),
                        "description": status.get("description", ""),
                    }
                    for status in schema.get("status_options", [])
                ]
        return []

    def _add_category_to_schema(self, category_data):
        """Add a new category to the schema and update DynamoDB"""
        current_schemas = self.state.get("ticket_schema", [])

        # Create new schema entry
        new_schema = {
            "uuid": f"{category_data['name'].lower()}_schema",
            "category": category_data["name"],
            "description": category_data["description"],
            "status_options": [],
            "subcategories": [],
        }

        # Add to current schemas
        current_schemas.append(new_schema)

        # Update DynamoDB
        key = {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}

        # Format the update expression and attributes
        update_expression = "SET schemas = :schemas"
        expression_attribute_values = {
            ":schemas": {"L": self._format_schemas_for_dynamo(current_schemas)}
        }

        # Update DynamoDB
        self.dynamo_adapter.update_item(
            key, update_expression, expression_attribute_values
        )

        # Update local state
        self.state.set("ticket_schema", current_schemas)
        self.state.set(
            "ticket_categories",
            [schema.get("category", "") for schema in current_schemas],
        )
        self._category_column.refresh()

    def _add_subcategory_to_schema(self, subcategory_data):
        """Add a new subcategory to the selected category in the schema"""
        current_schemas = self.state.get("ticket_schema", [])
        selected_category = self.state.get("selected_category")

        # Find the schema for the selected category
        for schema in current_schemas:
            if schema.get("category") == selected_category:
                # Create new subcategory entry
                new_subcategory = {
                    "subcategory": subcategory_data["name"],
                    "description": subcategory_data["description"],
                }

                # Add to current subcategories
                schema["subcategories"].append(new_subcategory)
                break

        # Update DynamoDB
        key = {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}

        # Format the update expression and attributes
        update_expression = "SET schemas = :schemas"
        expression_attribute_values = {
            ":schemas": {"L": self._format_schemas_for_dynamo(current_schemas)}
        }

        # Update DynamoDB
        self.dynamo_adapter.update_item(
            key, update_expression, expression_attribute_values
        )

        # Update local state
        self.state.set("ticket_schema", current_schemas)
        self.state.set(
            "ticket_subcategories", self._get_subcategories(selected_category)
        )
        self._subcategory_column.refresh()

    def _format_schemas_for_dynamo(self, schemas):
        """Convert schemas to DynamoDB format"""
        formatted_schemas = []
        for schema in schemas:
            formatted_schema = {
                "M": {
                    "uuid": {"S": schema["uuid"]},
                    "category": {"S": schema["category"]},
                    "description": {"S": schema["description"]},
                    "status_options": {
                        "L": [
                            {
                                "M": {
                                    "status": {"S": status["status"]},
                                    "description": {"S": status["description"]},
                                }
                            }
                            for status in schema.get("status_options", [])
                        ]
                    },
                    "subcategories": {
                        "L": [
                            {
                                "M": {
                                    "subcategory": {"S": sub["subcategory"]},
                                    "description": {"S": sub["description"]},
                                }
                            }
                            for sub in schema.get("subcategories", [])
                        ]
                    },
                }
            }
            formatted_schemas.append(formatted_schema)
        return formatted_schemas

    def _edit_category(self, category_data, old_category):
        """Edit an existing category in the schema"""
        current_schemas = self.state.get("ticket_schema", [])

        # Find and update the category
        for schema in current_schemas:
            if schema.get("category") == old_category:
                schema["category"] = category_data["name"]
                schema["description"] = category_data["description"]
                break

        # Update DynamoDB and local state
        self._update_schema_in_db(current_schemas)
        self.state.set("ticket_schema", current_schemas)
        self.state.set(
            "ticket_categories",
            [schema.get("category", "") for schema in current_schemas],
        )
        self._category_column.refresh()

    def _edit_subcategory(self, subcategory_data, old_subcategory):
        """Edit an existing subcategory in the schema"""
        current_schemas = self.state.get("ticket_schema", [])
        selected_category = self.state.get("selected_category")

        # Find and update the subcategory
        for schema in current_schemas:
            if schema.get("category") == selected_category:
                for sub in schema.get("subcategories", []):
                    if sub.get("subcategory") == old_subcategory:
                        sub["subcategory"] = subcategory_data["name"]
                        sub["description"] = subcategory_data["description"]
                        break
                break

        # Update DynamoDB and local state
        self._update_schema_in_db(current_schemas)
        self.state.set("ticket_schema", current_schemas)
        self.state.set(
            "ticket_subcategories", self._get_subcategories(selected_category)
        )
        self._subcategory_column.refresh()

    def _edit_status_option(self, status_data, old_status):
        """Edit an existing status option in the schema"""
        current_schemas = self.state.get("ticket_schema", [])
        selected_category = self.state.get("selected_category")

        # Find and update the status option
        for schema in current_schemas:
            if schema.get("category") == selected_category:
                for status in schema.get("status_options", []):
                    if status.get("status") == old_status["status"]:
                        status["status"] = status_data["name"]
                        status["description"] = status_data["description"]
                        break
                break

        # Update DynamoDB and local state
        self._update_schema_in_db(current_schemas)
        self.state.set("ticket_schema", current_schemas)
        self.state.set(
            "ticket_status_options", self._get_status_options(selected_category)
        )
        self._status_options_column.refresh()

    def _update_schema_in_db(self, current_schemas):
        """Helper method to update the schema in DynamoDB"""
        key = {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}
        update_expression = "SET schemas = :schemas"
        expression_attribute_values = {
            ":schemas": {"L": self._format_schemas_for_dynamo(current_schemas)}
        }
        self.dynamo_adapter.update_item(
            key, update_expression, expression_attribute_values
        )

    @ui.refreshable
    def _category_column(self):
        def _add_category():
            # Create dialog for adding new category
            with ui.dialog() as dialog, ui.card():
                ui.label("Add New Category").classes("text-lg font-bold mb-4")
                category_name = ui.input("Category Name").classes("w-full")
                category_description = ui.input("Description").classes("w-full")

                def save_category():
                    if not category_name.value:
                        ui.notify("Category name is required", type="negative")
                        return

                    category_data = {
                        "name": category_name.value,
                        "description": category_description.value or "",
                    }

                    self._add_category_to_schema(category_data)
                    dialog.close()
                    ui.notify("Category added successfully")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save_category)
            dialog.open()

        with ui.column().style("width:100%;display:flex;flex:1;height:100%;"):
            with ui.card().style(
                "width:100%;height:100%;display:flex;flex-direction:column;"
            ):
                with ui.row().classes("w-full border-b border-gray-200 pb-2"):
                    with ui.column().classes("flex flex-1"):
                        ui.label("Categories").classes("text-lg font-bold")
                    with ui.column():
                        ui.button(icon="o_add", on_click=_add_category)
                with ui.scroll_area().classes("w-full h-[100%]"):
                    if self.state.get("ticket_categories"):
                        with ui.list().props("bordered separator").classes(
                            "w-full h-[100%]"
                        ):
                            for category in self.state.get("ticket_categories"):
                                with ui.item().classes("w-full"):
                                    with ui.item_section().classes("cursor-pointer").on(
                                        "click",
                                        lambda c=category: self._select_category(c),
                                    ):
                                        ui.label(category)
                                    with ui.item_section().props("side"):
                                        ui.button(
                                            icon="o_edit",
                                            on_click=lambda c=category: self._show_edit_dialog(
                                                c
                                            ),
                                        ).props("flat dense")

    def _select_category(self, category):
        """Handle category selection"""
        self.state.set("selected_category", category)
        self.state.set("ticket_subcategories", self._get_subcategories(category))
        self.state.set("ticket_status_options", self._get_status_options(category))
        self._subcategory_column.refresh()
        self._status_options_column.refresh()

    def _show_edit_dialog(self, category):
        """Show edit dialog for category"""
        with ui.dialog() as dialog, ui.card():
            ui.label("Edit Category").classes("text-lg font-bold mb-4")
            category_name = ui.input("Category Name", value=category).classes("w-full")
            category_description = ui.input("Description").classes("w-full")

            def save_edit():
                if not category_name.value:
                    ui.notify("Category name is required", type="negative")
                    return

                category_data = {
                    "name": category_name.value,
                    "description": category_description.value or "",
                }

                self._edit_category(category_data, category)
                dialog.close()
                ui.notify("Category updated successfully")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save", on_click=save_edit)
        dialog.open()

    @ui.refreshable
    def _subcategory_column(self):
        def _add_subcategory():
            if not self.state.get("selected_category"):
                ui.notify("Please select a category first", type="negative")
                return

            # Create dialog for adding new subcategory
            with ui.dialog() as dialog, ui.card():
                ui.label("Add New Subcategory").classes("text-lg font-bold mb-4")
                subcategory_name = ui.input("Subcategory Name").classes("w-full")
                subcategory_description = ui.input("Description").classes("w-full")

                def save_subcategory():
                    if not subcategory_name.value:
                        ui.notify("Subcategory name is required", type="negative")
                        return

                    subcategory_data = {
                        "name": subcategory_name.value,
                        "description": subcategory_description.value or "",
                    }

                    self._add_subcategory_to_schema(subcategory_data)
                    dialog.close()
                    ui.notify("Subcategory added successfully")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save_subcategory)
            dialog.open()

        def _select_status_options(subcategory):
            self.state.set("selected_subcategory", subcategory)
            self.state.set(
                "ticket_status_options",
                self._get_status_options(self.state.get("selected_category")),
            )
            self._status_options_column.refresh()

        def _show_edit_dialog(subcategory):
            with ui.dialog() as dialog, ui.card():
                ui.label("Edit Subcategory").classes("text-lg font-bold mb-4")
                subcategory_name = ui.input(
                    "Subcategory Name", value=subcategory
                ).classes("w-full")
                subcategory_description = ui.input("Description").classes("w-full")

                def save_edit():
                    if not subcategory_name.value:
                        ui.notify("Subcategory name is required", type="negative")
                        return

                    subcategory_data = {
                        "name": subcategory_name.value,
                        "description": subcategory_description.value or "",
                    }

                    self._edit_subcategory(subcategory_data, subcategory)
                    dialog.close()
                    ui.notify("Subcategory updated successfully")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save_edit)
            dialog.open()

        with ui.column().style("width:100%;display:flex;flex:1;height:100%;"):
            with ui.card().style(
                "width:100%;height:100%;display:flex;flex-direction:column;"
            ):
                with ui.row().classes("w-full border-b border-gray-200 pb-2"):
                    with ui.column().classes("flex flex-1"):
                        ui.label("Sub-Categories").classes("text-lg font-bold")
                    with ui.column():
                        ui.button(icon="o_add", on_click=_add_subcategory)
                with ui.scroll_area().classes("w-full h-[100%]"):
                    if self.state.get("selected_category"):
                        with ui.list().props("bordered separator").classes(
                            "w-full h-[100%]"
                        ):
                            for subcategory in self.state.get(
                                "ticket_subcategories", []
                            ):
                                with ui.item().classes("w-full"):
                                    with ui.item_section():
                                        with ui.row().classes("w-full items-center"):
                                            with ui.column().classes("flex-1"):
                                                ui.label(subcategory)
                                            with ui.column():
                                                ui.button(
                                                    icon="o_edit",
                                                    on_click=lambda s=subcategory: _show_edit_dialog(
                                                        s
                                                    ),
                                                ).props("flat dense")

    def _add_status_option_to_schema(self, status_data):
        """Add a new status option to the selected category in the schema"""
        current_schemas = self.state.get("ticket_schema", [])
        selected_category = self.state.get("selected_category")

        # Find the schema for the selected category
        for schema in current_schemas:
            if schema.get("category") == selected_category:
                # Create new status option entry
                new_status = {
                    "status": status_data["name"],
                    "description": status_data["description"],
                }

                # Add to current status options
                schema["status_options"].append(new_status)
                break

        # Update DynamoDB
        key = {"uuid": {"S": "ticket_system"}, "tag": {"S": "ticket_system_schema"}}

        # Format the update expression and attributes
        update_expression = "SET schemas = :schemas"
        expression_attribute_values = {
            ":schemas": {"L": self._format_schemas_for_dynamo(current_schemas)}
        }

        # Update DynamoDB
        self.dynamo_adapter.update_item(
            key, update_expression, expression_attribute_values
        )

        # Update local state
        self.state.set("ticket_schema", current_schemas)
        self.state.set(
            "ticket_status_options", self._get_status_options(selected_category)
        )
        self._status_options_column.refresh()

    @ui.refreshable
    def _status_options_column(self):
        def _add_status_option():
            if not self.state.get("selected_category"):
                ui.notify("Please select a category first", type="negative")
                return

            # Create dialog for adding new status option
            with ui.dialog() as dialog, ui.card():
                ui.label("Add New Status Option").classes("text-lg font-bold mb-4")
                status_name = ui.input("Status Name").classes("w-full")
                status_description = ui.input("Description").classes("w-full")

                def save_status():
                    if not status_name.value:
                        ui.notify("Status name is required", type="negative")
                        return

                    status_data = {
                        "name": status_name.value,
                        "description": status_description.value or "",
                    }

                    self._add_status_option_to_schema(status_data)
                    dialog.close()
                    ui.notify("Status option added successfully")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save_status)
            dialog.open()

        def _show_edit_dialog(status_option):
            with ui.dialog() as dialog, ui.card():
                ui.label("Edit Status Option").classes("text-lg font-bold mb-4")
                status_name = ui.input(
                    "Status Name", value=status_option["status"]
                ).classes("w-full")
                status_description = ui.input(
                    "Description", value=status_option["description"]
                ).classes("w-full")

                def save_edit():
                    if not status_name.value:
                        ui.notify("Status name is required", type="negative")
                        return

                    status_data = {
                        "name": status_name.value,
                        "description": status_description.value or "",
                    }

                    self._edit_status_option(status_data, status_option)
                    dialog.close()
                    ui.notify("Status option updated successfully")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close).props("flat")
                    ui.button("Save", on_click=save_edit)
            dialog.open()

        with ui.column().style("width:100%;display:flex;flex:1;height:100%;"):
            with ui.card().style(
                "width:100%;height:100%;display:flex;flex-direction:column;"
            ):
                with ui.row().classes("w-full border-b border-gray-200 pb-2"):
                    with ui.column().classes("flex flex-1"):
                        ui.label("Status Options").classes("text-lg font-bold")
                    with ui.column():
                        ui.button(icon="o_add", on_click=_add_status_option)
                with ui.scroll_area().classes("w-full h-[100%]"):
                    if self.state.get("selected_category"):
                        status_options = self._get_status_options(
                            self.state.get("selected_category")
                        )
                        with ui.list().props("bordered separator").classes(
                            "w-full h-[100%]"
                        ):
                            for status_option in status_options:
                                with ui.item().classes("w-full"):
                                    with ui.item_section():
                                        with ui.row().classes("w-full items-center"):
                                            with ui.column().classes("flex-1"):
                                                with ui.row():
                                                    ui.label(status_option["status"])
                                                    ui.label(
                                                        status_option["description"]
                                                    ).classes("text-gray-500 ml-2")
                                            with ui.column():
                                                ui.button(
                                                    icon="o_edit",
                                                    on_click=lambda s=status_option: _show_edit_dialog(
                                                        s
                                                    ),
                                                ).props("flat dense")

    def content(self):
        def _separator():
            with ui.column().classes("flex justify-center items-center h-[100%] w-fit"):
                with ui.card().tight().classes(
                    f"w-[3rem] h-[3rem] flex justify-center items-center rounded-full bg-[{self.theme_manager.get_color('button-basic')}]"
                ):
                    ui.icon("o_keyboard_arrow_right").classes("text-4xl text-white")

        with ui.row().classes("w-full flex justify-end items-center"):
            ui.button(icon="o_save", on_click=lambda: ui.notify("Save"))
        with ui.row().style("display:flex;flex-direction:row;width:100%;height:80vh;"):
            self._category_column()
            _separator()
            self._subcategory_column()
            _separator()
            self._status_options_column()


def ticket_system_settings_page(storage_manager):
    page = SettingsTicketSystem(storage_manager)
    page.render()
