from nicegui import ui
from datetime import datetime

from config import config
from components.shared import StaticPage
from utils.helpers import dynamo_adapter
from models import ModificationRequest, ModificationOption, MortgageLoan


class Requests(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Requests",
            page_route="/requests",
            storage_manager=storage_manager,
            page_description="Requests",
        )
        self.dynamo_adapter = dynamo_adapter(config.aws_requests_table_name)
        self.screen_view = "view_all"
        self.selected_row = None
        self.requests_grid = None
        self.current_status = "pending"  # Track current status
        self.status_buttons = {}  # Store button references

    def content(self):
        with ui.column().classes("w-full"):
            with ui.tabs().classes("w-full") as tabs:
                requests_tab = ui.tab("Requests")
                permissions_tab = ui.tab("Permissions")

            with ui.tab_panels(tabs, value=requests_tab).classes("w-full"):
                with ui.tab_panel(requests_tab):
                    self.render_requests_tab()
                with ui.tab_panel(permissions_tab):
                    self.render_permissions_tab()

    def render_requests_tab(self):
        """Render the Requests tab content"""
        with ui.row().classes("w-full items-center justify-between mb-4"):
            ui.label("Modification Requests").classes("text-2xl")
            with ui.button_group().classes("bg-gray-100 rounded-lg"):
                self.status_buttons["pending"] = ui.button(
                    "Pending", on_click=lambda: self.filter_by_status("pending")
                ).classes(self.get_button_classes("pending"))

                self.status_buttons["hold"] = ui.button(
                    "Hold", on_click=lambda: self.filter_by_status("hold")
                ).classes(self.get_button_classes("hold"))

                self.status_buttons["completed"] = ui.button(
                    "Completed", on_click=lambda: self.filter_by_status("completed")
                ).classes(self.get_button_classes("completed"))

        if self.screen_view == "view_all":
            self.render_view_all()
        elif self.screen_view == "view_single":
            self.render_view_single()

    def render_permissions_tab(self):
        """Render the Permissions tab content"""
        with ui.grid(rows=2).classes("w-full h-[75vh] gap-2"):
            # Top row - ACL Table
            with ui.row().classes("w-full").style("height: 30vh;"):
                ui.label("Access Control List").classes("text-xl mb-2")
                self.acl_adapter = dynamo_adapter(config.aws_acl_table_name)
                acl_response = self.acl_adapter.scan()

                acl_columns = [
                    {"field": "uip", "headerName": "IP Address"},
                    {"field": "status", "headerName": "Status"},
                    {"field": "first_name", "headerName": "First Name"},
                    {"field": "last_name", "headerName": "Last Name"},
                    {"field": "email_address", "headerName": "Email Address"},
                    {"field": "created_on", "headerName": "Created Date"},
                ]

                acl_data = []
                for item in acl_response:
                    formatted_item = self.acl_adapter._format_map(item)
                    acl_data.append(
                        {
                            "uip": formatted_item.get("uip", ""),
                            "status": formatted_item.get("status", ""),
                            "first_name": formatted_item.get("first_name", ""),
                            "last_name": formatted_item.get("last_name", ""),
                            "email_address": formatted_item.get("email_address", ""),
                            "created_on": formatted_item.get("created_on", ""),
                        }
                    )

                # Store the grid reference
                self.acl_grid = (
                    ui.aggrid(
                        {
                            "columnDefs": acl_columns,
                            "rowData": acl_data,
                            "rowSelection": "single",
                            "domLayout": "autoHeight",
                        }
                    )
                    .classes("w-full")
                    .style("height: 28vh;")
                    .on("cellClicked", self.handle_acl_row_click)
                )

            # Bottom row - Task Log Table
            with ui.row().classes("w-full").style("height: 30vh;"):
                ui.label("Permission Request Log").classes("text-xl mb-2")
                self.task_log_adapter = dynamo_adapter(config.aws_task_log_table_name)
                task_log_response = self.task_log_adapter.scan(
                    FilterExpression="#service = :service",
                    ExpressionAttributeValues={
                        ":service": {"S": "resolution_form_permission_request"}
                    },
                    ExpressionAttributeNames={"#service": "service"},
                )

                task_log_columns = [
                    {"field": "ip", "headerName": "IP Address"},
                    {"field": "status", "headerName": "Status"},
                    {"field": "first_name", "headerName": "First Name"},
                    {"field": "last_name", "headerName": "Last Name"},
                    {"field": "email_address", "headerName": "Email Address"},
                    {"field": "created_on", "headerName": "Created Date"},
                ]

                task_log_data = []
                for item in task_log_response:
                    formatted_item = self.task_log_adapter._format_map(item)
                    task_log_data.append(
                        {
                            "task_id": formatted_item.get("task_id", ""),
                            "ip": formatted_item.get("ip", ""),
                            "status": formatted_item.get("status", ""),
                            "first_name": formatted_item.get("first_name", ""),
                            "last_name": formatted_item.get("last_name", ""),
                            "email_address": formatted_item.get("email_address", ""),
                            "created_on": formatted_item.get("created_on", ""),
                        }
                    )

                self.task_log_grid = (
                    ui.aggrid(
                        {
                            "columnDefs": task_log_columns,
                            "rowData": task_log_data,
                            "rowSelection": "single",
                            "domLayout": "autoHeight",
                        }
                    )
                    .classes("w-full")
                    .style("height: 28vh;")
                    .on("cellClicked", self.handle_task_log_row_click)
                )

    def get_button_classes(self, status: str) -> str:
        """Return classes for button based on current status"""
        base_classes = "px-4 py-2 text-sm transition-all duration-200"
        if status == self.current_status:
            return f"{base_classes} bg-blue-600 text-white shadow-inner"
        return f"{base_classes} hover:bg-blue-100 text-gray-700"

    def update_button_styles(self):
        """Update the styles of all status buttons"""
        for status, button in self.status_buttons.items():
            button.classes(self.get_button_classes(status))

    def filter_by_status(self, status: str):
        """Filter requests by status and update the grid"""
        self.current_status = status
        self.update_button_styles()

        print(f"Filtering by status: {status}")  # Debug print

        response = self.dynamo_adapter.scan(
            FilterExpression="#status = :status",
            ExpressionAttributeValues={":status": {"S": status}},
            ExpressionAttributeNames={"#status": "status"},
        )

        print(f"DynamoDB Response: {response}")  # Debug print

        # Convert DynamoDB items to grid data format
        requests = []
        for item in response:
            formatted_item = self.dynamo_adapter._format_map(item)
            print(f"Formatted Item: {formatted_item}")  # Debug print

            try:
                request_data = {
                    "uid": formatted_item.get("uid", ""),
                    "loan_number": formatted_item.get("loan_number", ""),
                    "borrower_name": f"{formatted_item.get('first_name', '')} {formatted_item.get('last_name', '')}",
                    "requested_payment": f"${float(formatted_item.get('requested_monthly_payment', 0)):,.2f}",
                    "down_payment": f"${float(formatted_item.get('requested_down_payment', 0)):,.2f}",
                    "payoff_total": f"${float(formatted_item.get('payoff_total_amount_due', 0)):,.2f}",
                    "payoff_good_till": formatted_item.get("payoff_good_till", ""),
                    "status": formatted_item.get("status", "").title(),
                    "raw_data": formatted_item,
                }
                requests.append(request_data)
            except Exception as e:
                print(f"Error processing item: {e}")  # Debug print
                continue

        print(f"Processed Requests: {requests}")  # Debug print

        # Update the grid with new data
        if self.requests_grid:
            print("Updating grid with data")  # Debug print
            self.requests_grid.options["rowData"] = requests
            self.requests_grid.update()
        else:
            print("Grid not initialized")  # Debug print

    def render_view_all(self):
        # Initial load with pending status
        self.filter_by_status("pending")

        # Create AgGrid table with columns matching the actual data structure
        columns = [
            {"field": "uid", "headerName": "Request ID"},
            {"field": "loan_number", "headerName": "Loan Number"},
            {"field": "borrower_name", "headerName": "Borrower Name"},
            {"field": "requested_payment", "headerName": "Requested Payment"},
            {"field": "down_payment", "headerName": "Down Payment"},
            {"field": "payoff_total", "headerName": "Payoff Amount"},
            {"field": "payoff_good_till", "headerName": "Payoff Good Till"},
            {"field": "status", "headerName": "Status"},
        ]

        self.requests_grid = (
            ui.aggrid(
                {
                    "columnDefs": columns,
                    "rowData": [],  # Initially empty, will be populated by filter_by_status
                    "rowSelection": "single",
                    "domLayout": "autoHeight",
                }
            )
            .classes("w-full")
            .on("cellClicked", self.handle_row_click)
        )

    def render_view_single(self):
        # This will be implemented later to show detailed view
        pass

    def handle_row_click(self, e):
        """Handle row click event in the AgGrid table"""
        self.selected_row = e.args["data"]
        self.screen_view = "view_single"
        self.update()

    def handle_acl_row_click(self, e):
        """Handle ACL table row click"""
        row_data = e.args["data"]

        with ui.dialog() as dialog, ui.card():
            ui.label("Edit Access Control Entry").classes("text-xl mb-4")

            # Create input fields
            ip_input = ui.input("IP Address", value=row_data["uip"])
            status_input = ui.input("Status", value=str(row_data["status"]))
            first_name_input = ui.input("First Name", value=row_data["first_name"])
            last_name_input = ui.input("Last Name", value=row_data["last_name"])
            email_input = ui.input("Email Address", value=row_data["email_address"])

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Cancel", on_click=dialog.close).classes(
                    "bg-gray-500 text-white"
                )

                async def update_acl():
                    try:
                        # Prepare the key
                        key = {"uip": {"S": row_data["uip"]}}

                        # Prepare update expression and attributes
                        update_expression = "SET "
                        expression_attribute_values = {}
                        expression_attribute_names = {}

                        fields = {
                            "status": status_input.value,
                            "first_name": first_name_input.value,
                            "last_name": last_name_input.value,
                            "email_address": email_input.value,
                        }

                        # Build the expressions
                        for i, (field, value) in enumerate(fields.items()):
                            update_expression += f"#{field} = :{field}"
                            expression_attribute_values[f":{field}"] = {"S": value}
                            expression_attribute_names[f"#{field}"] = field
                            if i < len(fields) - 1:
                                update_expression += ", "

                        # Update the record
                        result = self.acl_adapter.update_item(
                            key=key,
                            update_expression=update_expression,
                            expression_attribute_values=expression_attribute_values,
                            expression_attribute_names=expression_attribute_names,
                        )

                        if result is not None:
                            dialog.close()
                            ui.notify("Record updated successfully")

                            # Refresh the table data
                            acl_response = self.acl_adapter.scan()
                            acl_data = []
                            for item in acl_response:
                                formatted_item = self.acl_adapter._format_map(item)
                                acl_data.append(
                                    {
                                        "uip": formatted_item.get("uip", ""),
                                        "status": formatted_item.get("status", ""),
                                        "first_name": formatted_item.get(
                                            "first_name", ""
                                        ),
                                        "last_name": formatted_item.get(
                                            "last_name", ""
                                        ),
                                        "email_address": formatted_item.get(
                                            "email_address", ""
                                        ),
                                        "created_on": formatted_item.get(
                                            "created_on", ""
                                        ),
                                    }
                                )

                            # Update the grid with new data
                            self.acl_grid.options["rowData"] = acl_data
                            self.acl_grid.update()
                        else:
                            ui.notify("Failed to update record", type="error")

                    except Exception as e:
                        print(f"Error in update_acl: {e}")
                        ui.notify("Failed to update record", type="error")

                ui.button("Update", on_click=update_acl).classes(
                    "bg-blue-500 text-white"
                )

            dialog.open()

    def handle_task_log_row_click(self, e):
        """Handle Task Log table row click"""
        row_data = e.args["data"]

        with ui.dialog() as dialog, ui.card():
            ui.label("Permission Request Details").classes("text-xl mb-4")

            # Display request details
            ui.label(f"IP Address: {row_data['ip']}")
            ui.label(f"Status: {row_data['status']}")
            ui.label(f"Name: {row_data['first_name']} {row_data['last_name']}")
            ui.label(f"Email: {row_data['email_address']}")
            ui.label(f"Created On: {row_data['created_on']}")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):

                async def deny_request():
                    try:
                        # Delete using the composite key (ip + service)
                        delete_key = {
                            "ip": {"S": row_data["ip"]},
                            "service": {"S": "resolution_form_permission_request"},
                        }

                        self.task_log_adapter.delete_item(key=delete_key)
                        dialog.close()
                        ui.notify("Request denied")

                        # Refresh task log table
                        task_log_response = self.task_log_adapter.scan(
                            FilterExpression="#service = :service",
                            ExpressionAttributeValues={
                                ":service": {"S": "resolution_form_permission_request"}
                            },
                            ExpressionAttributeNames={"#service": "service"},
                        )

                        task_log_data = []
                        for item in task_log_response:
                            formatted_item = self.task_log_adapter._format_map(item)
                            task_log_data.append(
                                {
                                    "ip": formatted_item.get("ip", ""),
                                    "status": formatted_item.get("status", ""),
                                    "first_name": formatted_item.get("first_name", ""),
                                    "last_name": formatted_item.get("last_name", ""),
                                    "email_address": formatted_item.get(
                                        "email_address", ""
                                    ),
                                    "created_on": formatted_item.get("created_on", ""),
                                }
                            )

                        # Update task log grid
                        self.task_log_grid.options["rowData"] = task_log_data
                        self.task_log_grid.update()

                    except Exception as e:
                        print(f"Error in deny_request: {e}")
                        ui.notify("Failed to deny request", type="error")

                async def approve_request():
                    try:
                        # Create new ACL entry
                        acl_item = {
                            "uip": {"S": row_data["ip"]},
                            "status": {"S": "ALLOW"},
                            "first_name": {"S": row_data["first_name"]},
                            "last_name": {"S": row_data["last_name"]},
                            "email_address": {"S": row_data["email_address"]},
                            "created_on": {"S": row_data["created_on"]},
                        }

                        # Add the ACL entry
                        result = self.acl_adapter.put_item(acl_item)

                        if result is not None:
                            # Delete using the composite key (ip + service)
                            delete_key = {
                                "task_id": {"S": row_data["task_id"]},
                                "service": {"S": "resolution_form_permission_request"},
                            }

                            self.task_log_adapter.delete_item(key=delete_key)

                            dialog.close()
                            ui.notify("Request approved")

                            # Refresh both tables
                            acl_response = self.acl_adapter.scan()
                            acl_data = []
                            for item in acl_response:
                                formatted_item = self.acl_adapter._format_map(item)
                                acl_data.append(
                                    {
                                        "uip": formatted_item.get("uip", ""),
                                        "status": formatted_item.get("status", ""),
                                        "first_name": formatted_item.get(
                                            "first_name", ""
                                        ),
                                        "last_name": formatted_item.get(
                                            "last_name", ""
                                        ),
                                        "email_address": formatted_item.get(
                                            "email_address", ""
                                        ),
                                        "created_on": formatted_item.get(
                                            "created_on", ""
                                        ),
                                    }
                                )

                            # Update ACL grid
                            self.acl_grid.options["rowData"] = acl_data
                            self.acl_grid.update()

                            # Refresh task log table
                            task_log_response = self.task_log_adapter.scan(
                                FilterExpression="#service = :service",
                                ExpressionAttributeValues={
                                    ":service": {
                                        "S": "resolution_form_permission_request"
                                    }
                                },
                                ExpressionAttributeNames={"#service": "service"},
                            )

                            task_log_data = []
                            for item in task_log_response:
                                formatted_item = self.task_log_adapter._format_map(item)
                                task_log_data.append(
                                    {
                                        "ip": formatted_item.get("ip", ""),
                                        "status": formatted_item.get("status", ""),
                                        "first_name": formatted_item.get(
                                            "first_name", ""
                                        ),
                                        "last_name": formatted_item.get(
                                            "last_name", ""
                                        ),
                                        "email_address": formatted_item.get(
                                            "email_address", ""
                                        ),
                                        "created_on": formatted_item.get(
                                            "created_on", ""
                                        ),
                                    }
                                )

                            # Update task log grid
                            self.task_log_grid.options["rowData"] = task_log_data
                            self.task_log_grid.update()
                        else:
                            ui.notify("Failed to approve request", type="error")

                    except Exception as e:
                        print(f"Error in approve_request: {e}")
                        ui.notify("Failed to approve request", type="error")

                ui.button("Deny", on_click=deny_request).classes(
                    "bg-red-500 text-white"
                )
                ui.button("Approve", on_click=approve_request).classes(
                    "bg-green-500 text-white"
                )

            dialog.open()


def requests_page(storage_manager):
    page = Requests(storage_manager)
    page.render()
