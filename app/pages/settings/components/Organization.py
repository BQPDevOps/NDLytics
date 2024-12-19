from nicegui import ui
from datetime import datetime
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from models import RoleModel, CompanyModel
from config import config
from modules import TokenManager, TokenType
from enum import Enum
import uuid


class RoleView(Enum):
    TABLE_VIEW = "role_tab_view"
    NEW_VIEW = "role_tab_new"
    EDIT_VIEW = "role_tab_edit"


class OrganizationComponent:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.cognito_middleware = CognitoMiddleware()
        self.companies_dynamo_middleware = DynamoMiddleware(
            config.aws_companies_table_name
        )
        self.company_roles = []
        self.user_company = None
        self.define_role_view = RoleView.TABLE_VIEW.value
        self.user_checkboxes = []
        self.selected_roles = []
        self.role_checkboxes = []

        # Initialize default RoleModel with assigned_to
        self.new_role_config = RoleModel(
            role_id="",
            role_name="",
            role_description="",
            role_reports_to=[],
            role_reporting_team=[],
            role_responsibilities=[],
            role_displayed_in_org=False,
            assigned_to=[],
            created_on="",
            created_by="",
            updated_on="",
            updated_by="",
        )

        self._get_user_company()

    def _get_user_company(self):
        try:
            # Get user ID from token
            token = self.session_manager.get("id_token")
            token_manager = TokenManager(TokenType.ID, token)
            user = token_manager.get_decoded_token().dict()
            self.user_id = user.get("sub")

            # Get company_id from user's Cognito attributes
            company_id = self.cognito_middleware.get_all_custom_attributes(
                self.session_manager.get("username")
            ).get("custom:company_id")

            # Get company record from DynamoDB
            company_record = self.companies_dynamo_middleware.get_item(
                {"company_id": {"S": company_id}}
            )

            if company_record:
                # Convert DynamoDB record to CompanyModel
                self.user_company = CompanyModel.from_dynamo_item(company_record)
                # Set company roles from company record
                self.company_roles = self.user_company.company_roles
            else:
                print(f"No company record found for company_id: {company_id}")

        except Exception as e:
            print(f"Error getting user company: {str(e)}")

    def handle_select_all(self):
        pass

    def handle_select_all_roles(self, e):
        """Handle select all checkbox for roles"""
        if e.value:
            self.selected_roles = self.company_roles.copy()
        else:
            self.selected_roles = []

        # Update all checkboxes in the list
        for checkbox in self.role_checkboxes:
            checkbox.value = e.value

        self._render_actions_bar.refresh()

    def handle_role_select(self, role, e):
        """Handle individual role selection"""
        if e.value:
            if role not in self.selected_roles:
                self.selected_roles.append(role)
        else:
            if role in self.selected_roles:
                self.selected_roles.remove(role)

        self._render_actions_bar.refresh()

    @ui.refreshable
    def _render_actions_bar(self):
        """Render action buttons for roles"""
        num_selected = len(self.selected_roles)
        delete_text = f"({num_selected}) Delete" if num_selected > 0 else "Delete"
        edit_disabled = num_selected != 1

        with ui.row().classes("h-full items-center gap-2"):
            ui.button(icon="delete", text=delete_text).props(
                f"size=sm {'disable' if num_selected == 0 else ''}"
            ).style("min-width: 130px;").tooltip("Delete")
            ui.button(
                icon="edit",
                text="Edit",
                on_click=self.handle_edit_role,  # Add edit handler
            ).props(f"size=sm {'disable' if edit_disabled else ''}").style(
                "min-width: 130px;"
            ).tooltip(
                "Edit"
            )
            ui.button("New Role", on_click=self.handle_new_role).props("size=sm").style(
                "min-width: 130px;"
            )

    def _render_role_tab_view(self):
        with ui.column().classes("w-full h-full"):
            with ui.row().style(
                """
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        padding-left:0.5rem;
                        padding-right:0.5rem;
                        width:100%;
                        height:2.5rem;
                        background-color:#FFFFFF;
                        border-radius:5px;
                        border:1px solid rgba(192,192,192,0.3);
                        box-shadow:0 0 0 1px rgba(192,192,192,0.4);
                        background-color:rgba(120,120,120,0.2);
                        """
            ):
                ui.label("Organization Roles").style(
                    "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                )
                self._render_actions_bar()
            with ui.column().classes("w-full h-[70vh] gap-0"):
                with ui.column().classes("w-full px-4"):
                    with ui.card().tight().classes("w-full"):
                        with ui.list().classes("w-full").props("bordered separator"):
                            with ui.item().classes("w-full"):
                                with ui.item_section().props("side").style(
                                    "padding-right: 2rem; padding-left: 0.5rem; min-width: 100px;display:flex;justify-content:center;align-items:center;"
                                ):
                                    ui.label("Select All").style(
                                        "font-size:0.7rem;font-weight:bold;color:#4A4A4A;white-space:nowrap;"
                                    )
                                    ui.checkbox(
                                        on_change=self.handle_select_all_roles
                                    ).props("dense")
                                with ui.row().classes(
                                    "w-full grid grid-cols-3 text-center gap-4"
                                ):
                                    ui.label("Role Name").style(
                                        "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                    )
                                    ui.label("Role Description").style(
                                        "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                    )
                                    ui.label("Assigned To").style(
                                        "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                    )
                with ui.scroll_area().classes("w-full h-[76vh]"):
                    with ui.list().props("bordered separator").classes("w-full h-full"):
                        self.role_checkboxes = []  # Reset checkboxes list
                        for role in self.company_roles:
                            with ui.item().classes("w-full"):
                                with ui.item_section().props("side").style(
                                    "padding-right: 2rem; padding-left: 0.5rem; min-width: 100px;display:flex;justify-content:center;align-items:center;"
                                ):
                                    checkbox = ui.checkbox(
                                        on_change=lambda e, r=role: self.handle_role_select(
                                            r, e
                                        )
                                    ).props("dense")
                                    self.role_checkboxes.append(checkbox)
                                with ui.row().classes(
                                    "w-full justify-center h-full grid grid-cols-3 text-center gap-4"
                                ):
                                    ui.label(role.role_name).style(
                                        "font-size:1rem;color:#4A4A4A;"
                                    )
                                    ui.label(role.role_description).style(
                                        "font-size:1rem;color:#4A4A4A;"
                                    )
                                    ui.label(
                                        len(role.assigned_to) if role.assigned_to else 0
                                    ).style("font-size:1rem;color:#4A4A4A;")

    def handle_cancel_new_role(self):
        """Handle click of Cancel button in new role form"""
        # Reset new role config
        self.new_role_config = None
        # Change view back to table view
        self.define_role_view = RoleView.TABLE_VIEW.value
        # Refresh the view
        self.render_define_role_tab.refresh()

    def handle_add_responsibility(self):
        """Handle click of Add Responsibility button"""
        dialog = ui.dialog().props("size=medium")
        responsibility = {"text": ""}  # Use dict to store input value

        with dialog, ui.card().classes("w-full"):
            with ui.column().classes("w-full h-full p-4 gap-4"):
                ui.label("New Role Responsibility").style(
                    "font-size:1.2rem;font-weight:bold;color:#4A4A4A;"
                )
                ui.input(placeholder="Enter responsibility...").classes("w-full").props(
                    "outlined dense"
                ).bind_value(responsibility, "text")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=dialog.close).props("size=sm")
                    ui.button(
                        "Add",
                        on_click=lambda: self.save_responsibility(
                            responsibility["text"], dialog
                        ),
                    ).props("size=sm")

        dialog.open()

    def save_responsibility(self, text: str, dialog):
        """Save new responsibility to role config"""
        if text.strip():  # Only add if text is not empty
            if not self.new_role_config.role_responsibilities:
                self.new_role_config.role_responsibilities = []
            self.new_role_config.role_responsibilities.append(text)
            dialog.close()
            self.render_define_role_tab.refresh()

    def handle_create_role(self):
        """Handle click of Create Role button"""
        try:
            # Generate new role ID
            new_role_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()

            # Create validated RoleModel
            validated_role = RoleModel(
                role_id=new_role_id,
                role_name=self.new_role_config.role_name,
                role_description=self.new_role_config.role_description,
                role_reports_to=self.new_role_config.role_reports_to,
                role_reporting_team=self.new_role_config.role_reporting_team,
                role_responsibilities=self.new_role_config.role_responsibilities,
                role_displayed_in_org=self.new_role_config.role_displayed_in_org,
                assigned_to=[],
                created_on=current_time,
                created_by=self.user_id,
                updated_on=current_time,
                updated_by=self.user_id,
            )

            # Add new role to company roles
            if not self.user_company.company_roles:
                self.user_company.company_roles = []
            self.user_company.company_roles.append(validated_role)

            # Convert company model to DynamoDB format
            company_item = self.user_company.to_dynamo_item()

            # Update company record in DynamoDB
            self.companies_dynamo_middleware.put_item(company_item)

            # Update local company roles
            self.company_roles = self.user_company.company_roles

            # Reset view and form
            self.define_role_view = RoleView.TABLE_VIEW.value
            self.new_role_config = RoleModel(
                role_id="",
                role_name="",
                role_description="",
                role_reports_to=[],
                role_reporting_team=[],
                role_responsibilities=[],
                role_displayed_in_org=False,
                assigned_to=[],
                created_on="",
                created_by="",
                updated_on="",
                updated_by="",
            )

            # Refresh the view
            self.render_define_role_tab.refresh()
            self._render_org_chart.refresh()

            # Show success notification
            ui.notify("Role created successfully", type="positive")

        except Exception as e:
            print(f"Error creating role: {str(e)}")
            ui.notify(f"Error creating role: {str(e)}", type="negative")

    def get_related_roles(self):
        """Get roles that share reporting relationships with selected roles"""
        if not self.new_role_config.role_reports_to or not self.company_roles:
            return []

        related_roles = []
        for role in self.company_roles:
            # Check if any of the role's reports_to matches our selected reports_to
            if any(
                report_to in self.new_role_config.role_reports_to
                for report_to in role.role_reports_to
            ):
                related_roles.append(role)

        return related_roles

    def _render_role_tab_new(self):
        # Create options dictionary for role selection
        role_options = (
            {role.role_id: role.role_name for role in self.company_roles}
            if self.company_roles
            else {}
        )

        with ui.row().style(
            """
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding-left:0.5rem;
                    padding-right:0.5rem;
                    width:100%;
                    height:2.5rem;
                    background-color:#FFFFFF;
                    border-radius:5px;
                    border:1px solid rgba(192,192,192,0.3);
                    box-shadow:0 0 0 1px rgba(192,192,192,0.4);
                    background-color:rgba(120,120,120,0.2);
                    """
        ):
            ui.label("Define New Role").style(
                "font-size:1rem;font-weight:bold;color:#4A4A4A;"
            )
            with ui.row():
                ui.button("Cancel", on_click=self.handle_cancel_new_role).props(
                    "size=sm"
                ).style("min-width: 130px;")
                ui.button("Create Role", on_click=self.handle_create_role).props(
                    "size=sm"
                ).style("min-width: 130px;")
        with ui.grid(rows=3).classes("w-full h-[70vh] gap-0"):
            with ui.row().classes("row-span-1 w-full h-full"):
                ui.input(
                    label="Role Name", value=self.new_role_config.role_name
                ).classes("w-full").props("outlined dense").bind_value(
                    self.new_role_config, "role_name"
                )

                ui.textarea(
                    label="Role Description",
                    value=self.new_role_config.role_description,
                ).classes("w-full").props("outlined dense").bind_value(
                    self.new_role_config, "role_description"
                )
            with ui.row().classes("row-span-1 h-full w-full"):
                with ui.grid(columns=2).classes("w-full h-full"):
                    with ui.column().classes("col-span-1 p-2 gap-0"):
                        ui.label("Reports To").style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        ui.select(
                            options=role_options, multiple=True, label="Select Roles"
                        ).classes("w-full").props(
                            "use-chips outlined dense"
                        ).bind_value(
                            self.new_role_config, "role_reports_to"
                        )
                    with ui.column().classes("col-span-1 h-full"):
                        with ui.column().classes(
                            "w-full h-full rounded-lg border border-gray-300 mb-4 p-2"
                        ):
                            ui.label("Related Roles").style(
                                "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                            )
                            # Add related roles list
                            with ui.column().classes("w-full gap-0"):
                                with ui.scroll_area().classes("w-full h-[12vh]"):
                                    with ui.list().props("bordered separator").classes(
                                        "w-full h-full"
                                    ):
                                        related_roles = self.get_related_roles()
                                        if related_roles:
                                            for role in related_roles:
                                                with ui.item().props("dense").classes(
                                                    "w-full"
                                                ):
                                                    with ui.item_section():
                                                        ui.label(
                                                            text=role.role_name
                                                        ).style(
                                                            "font-size:1rem;color:#4A4A4A;"
                                                        )
                                        else:
                                            with ui.item().props("dense").classes(
                                                "w-full"
                                            ):
                                                with ui.item_section():
                                                    ui.label(
                                                        "No related roles found"
                                                    ).style(
                                                        "font-size:1rem;color:#4A4A4A;"
                                                    )
            with ui.row().classes("row-span-1 h-full w-full"):
                with ui.column().classes("w-full h-full"):
                    with ui.row().style(
                        """
                                display:flex;
                                justify-content:space-between;
                                align-items:center;
                                padding-left:0.5rem;
                                padding-right:0.5rem;
                                width:100%;
                                height:2.5rem;
                                background-color:#FFFFFF;
                                border-radius:5px;
                                border:1px solid rgba(192,192,192,0.3);
                                box-shadow:0 0 0 1px rgba(192,192,192,0.4);
                                background-color:rgba(120,120,120,0.2);
                                """
                    ):
                        ui.label("Define Responsibilities").style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        with ui.row():
                            ui.button(
                                icon="add",
                                on_click=self.handle_add_responsibility,
                            ).props("round size=sm")
                    # Display responsibilities list
                    if (
                        self.new_role_config
                        and self.new_role_config.role_responsibilities
                    ):
                        with ui.column().classes(
                            "w-full h-full rounded-lg border border-gray-300 justify-start"
                        ):
                            with ui.column().classes("w-full gap-0"):
                                with ui.card().tight().classes("w-full rounded-lg"):
                                    with ui.list().classes("w-full").props(
                                        "bordered separator"
                                    ):
                                        with ui.item():
                                            with ui.row().classes(
                                                "w-full grid grid-cols-2 gap-4 justify-start items-center"
                                            ):
                                                ui.label("Description").style(
                                                    "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                )
                                                ui.label("Actions").style(
                                                    "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                )
                                with ui.scroll_area().classes("w-full h-[10vh]"):
                                    with ui.list().props("bordered separator").classes(
                                        "w-full h-full"
                                    ):
                                        for (
                                            resp
                                        ) in self.new_role_config.role_responsibilities:
                                            with ui.item().props("dense").classes(
                                                "w-full"
                                            ):
                                                with ui.item_section():
                                                    ui.label(text=resp).style(
                                                        "font-size:1rem;color:#4A4A4A;"
                                                    )
                                                with ui.item_section().classes(
                                                    "w-full"
                                                ).props("side"):
                                                    ui.button(icon="delete").props(
                                                        "round size=sm"
                                                    )
                    else:
                        ui.label("No responsibilities defined")

    def handle_update_role(self):
        """Handle click of Update Role button"""
        try:
            current_time = datetime.now().isoformat()

            # Update timestamps
            self.new_role_config.updated_on = current_time
            self.new_role_config.updated_by = self.user_id

            # Find and update the role in company_roles
            for i, role in enumerate(self.user_company.company_roles):
                if role.role_id == self.new_role_config.role_id:
                    self.user_company.company_roles[i] = self.new_role_config
                    break

            # Convert company model to DynamoDB format
            company_item = self.user_company.to_dynamo_item()

            # Update company record in DynamoDB
            self.companies_dynamo_middleware.put_item(company_item)

            # Update local company roles
            self.company_roles = self.user_company.company_roles

            # Clear checkbox selections
            self.selected_roles = []
            for checkbox in self.role_checkboxes:
                checkbox.value = False

            # Reset view and form
            self.define_role_view = RoleView.TABLE_VIEW.value
            self.new_role_config = RoleModel(
                role_id="",
                role_name="",
                role_description="",
                role_reports_to=[],
                role_reporting_team=[],
                role_responsibilities=[],
                role_displayed_in_org=False,
                assigned_to=[],
                created_on="",
                created_by="",
                updated_on="",
                updated_by="",
            )

            # Refresh the views
            self.render_define_role_tab.refresh()
            self._render_actions_bar.refresh()
            self._render_org_chart.refresh()

            # Show success notification
            ui.notify("Role updated successfully", type="positive")

        except Exception as e:
            print(f"Error updating role: {str(e)}")
            ui.notify(f"Error updating role: {str(e)}", type="negative")

    def _render_role_tab_edit(self):
        """Render edit role form"""
        # Create options dictionary for role selection
        role_options = (
            {role.role_id: role.role_name for role in self.company_roles}
            if self.company_roles
            else {}
        )

        with ui.row().style(
            """
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding-left:0.5rem;
            padding-right:0.5rem;
            width:100%;
            height:2.5rem;
            background-color:#FFFFFF;
            border-radius:5px;
            border:1px solid rgba(192,192,192,0.3);
            box-shadow:0 0 0 1px rgba(192,192,192,0.4);
            background-color:rgba(120,120,120,0.2);
            """
        ):
            ui.label("Edit Role").style(
                "font-size:1rem;font-weight:bold;color:#4A4A4A;"
            )
            with ui.row():
                ui.button("Cancel", on_click=self.handle_cancel_new_role).props(
                    "size=sm"
                ).style("min-width: 130px;")
                ui.button("Update Role", on_click=self.handle_update_role).props(
                    "size=sm"
                ).style("min-width: 130px;")

        with ui.grid(rows=3).classes("w-full h-[70vh] gap-0"):
            with ui.row().classes("row-span-1 w-full h-full"):
                ui.input(
                    label="Role Name", value=self.new_role_config.role_name
                ).classes("w-full").props("outlined dense").bind_value(
                    self.new_role_config, "role_name"
                )

                ui.textarea(
                    label="Role Description",
                    value=self.new_role_config.role_description,
                ).classes("w-full").props("outlined dense").bind_value(
                    self.new_role_config, "role_description"
                )

            with ui.row().classes("row-span-1 h-full w-full"):
                with ui.grid(columns=2).classes("w-full h-full"):
                    with ui.column().classes("col-span-1 p-2 gap-0"):
                        ui.label("Reports To").style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        ui.select(
                            options=role_options,
                            multiple=True,
                            label="Select Roles",
                            value=self.new_role_config.role_reports_to,
                        ).classes("w-full").props(
                            "use-chips outlined dense"
                        ).bind_value(
                            self.new_role_config, "role_reports_to"
                        )

                    with ui.column().classes("col-span-1 h-full"):
                        # Related roles section (identical to new view)
                        with ui.column().classes(
                            "w-full h-full rounded-lg border border-gray-300 mb-4 p-2"
                        ):
                            ui.label("Related Roles").style(
                                "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                            )
                            # Add related roles list (identical to new view)
                            with ui.column().classes("w-full gap-0"):
                                with ui.scroll_area().classes("w-full h-[12vh]"):
                                    with ui.list().props("bordered separator").classes(
                                        "w-full h-full"
                                    ):
                                        related_roles = self.get_related_roles()
                                        if related_roles:
                                            for role in related_roles:
                                                with ui.item().props("dense").classes(
                                                    "w-full"
                                                ):
                                                    with ui.item_section():
                                                        ui.label(
                                                            text=role.role_name
                                                        ).style(
                                                            "font-size:1rem;color:#4A4A4A;"
                                                        )
                                        else:
                                            with ui.item().props("dense").classes(
                                                "w-full"
                                            ):
                                                with ui.item_section():
                                                    ui.label(
                                                        "No related roles found"
                                                    ).style(
                                                        "font-size:1rem;color:#4A4A4A;"
                                                    )

            with ui.row().classes("row-span-1 h-full w-full"):
                # Responsibilities section (identical to new view)
                with ui.column().classes("w-full h-full"):
                    with ui.row().style(
                        """
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        padding-left:0.5rem;
                        padding-right:0.5rem;
                        width:100%;
                        height:2.5rem;
                        background-color:#FFFFFF;
                        border-radius:5px;
                        border:1px solid rgba(192,192,192,0.3);
                        box-shadow:0 0 0 1px rgba(192,192,192,0.4);
                        background-color:rgba(120,120,120,0.2);
                        """
                    ):
                        ui.label("Define Responsibilities").style(
                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                        )
                        with ui.row():
                            ui.button(
                                icon="add",
                                on_click=self.handle_add_responsibility,
                            ).props("round size=sm")

                    # Display responsibilities list (identical to new view)
                    if (
                        self.new_role_config
                        and self.new_role_config.role_responsibilities
                    ):
                        with ui.column().classes(
                            "w-full h-full rounded-lg border border-gray-300 justify-start"
                        ):
                            with ui.column().classes("w-full gap-0"):
                                with ui.card().tight().classes("w-full rounded-lg"):
                                    with ui.list().classes("w-full").props(
                                        "bordered separator"
                                    ):
                                        with ui.item():
                                            with ui.row().classes(
                                                "w-full grid grid-cols-2 gap-4 justify-start items-center"
                                            ):
                                                ui.label("Description").style(
                                                    "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                )
                                                ui.label("Actions").style(
                                                    "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                )
                            with ui.scroll_area().classes("w-full h-[10vh]"):
                                with ui.list().props("bordered separator").classes(
                                    "w-full h-full"
                                ):
                                    for (
                                        resp
                                    ) in self.new_role_config.role_responsibilities:
                                        with ui.item().props("dense").classes("w-full"):
                                            with ui.item_section():
                                                ui.label(text=resp).style(
                                                    "font-size:1rem;color:#4A4A4A;"
                                                )
                                            with ui.item_section().classes(
                                                "w-full"
                                            ).props("side"):
                                                ui.button(icon="delete").props(
                                                    "round size=sm"
                                                )
                    else:
                        ui.label("No responsibilities defined")

    @ui.refreshable
    def render_define_role_tab(self):
        if self.define_role_view == "role_tab_view":
            self._render_role_tab_view()
        elif self.define_role_view == "role_tab_new":
            self._render_role_tab_new()
        elif self.define_role_view == "role_tab_edit":
            self._render_role_tab_edit()

    def _prepare_mermaid_chart(self):
        """Transform role data into Mermaid flowchart format with enhanced styling"""
        if not self.company_roles:
            return "graph TD\n  A[No Roles Defined]"

        # Start flowchart definition with styling
        mermaid_str = """
        %%{
          init: {
            'theme': 'base',
            'themeVariables': {
              'primaryColor': '#fff',
              'primaryTextColor': '#333',
              'primaryBorderColor': '#ccc',
              'lineColor': '#999',
              'fontSize': '16px'
            },
            'flowchart': {
              'htmlLabels': true,
              'curve': 'basis',
              'rankSpacing': 80,
              'nodeSpacing': 100,
              'padding': 20
            }
          }
        }%%\n
        graph TD\n
        """

        # Add nodes with enhanced styling
        for role in self.company_roles:
            team_size = len(role.assigned_to) if role.assigned_to else 0
            # Add custom styling to nodes
            mermaid_str += f"  {role.role_id}[\"{role.role_name}<br/><span style='font-size:14px;color:#666'>({team_size} members)</span>\"]:::roleNode\n"

        # Add connections
        for role in self.company_roles:
            for reports_to in role.role_reports_to:
                mermaid_str += f"  {reports_to} --> {role.role_id}\n"

        # Add custom class definitions
        mermaid_str += """
        classDef roleNode fill:#f0f7ff,stroke:#4a90e2,stroke-width:2px,rx:5px,ry:5px;
        classDef default fill:#fff,stroke:#333,stroke-width:1px;
        """

        return mermaid_str

    @ui.refreshable
    def _render_org_chart(self):
        """Render organizational chart using Mermaid with enhanced styling"""
        with ui.card().classes("w-full h-full flex items-center justify-center"):
            with ui.column().classes(
                "w-full h-full flex items-center justify-center p-4"
            ):
                ui.label(
                    self.user_company.company_name
                    if self.user_company
                    else "Organization Chart"
                ).style(
                    "font-size:1.5rem;font-weight:bold;color:#4A4A4A;margin-bottom:1rem;"
                )
                ui.mermaid(self._prepare_mermaid_chart()).classes(
                    "w-full h-[60vh] flex items-center justify-center"
                ).style(
                    """
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: #fafafa;
                    border-radius: 8px;
                    padding: 1rem;
                    """
                )

    def render(self):
        with ui.grid(columns=2).classes("w-full h-full"):
            with ui.column().classes("col-span-1"):
                with ui.tabs().classes("w-full") as tabs:
                    assign_tab = ui.tab("Assign Roles")
                    define_tab = ui.tab("Define Roles")
                with ui.tab_panels(tabs, value=define_tab).classes("w-full h-full"):
                    with ui.tab_panel(assign_tab).classes(
                        "w-full h-full rounded-lg border border-gray-300"
                    ):
                        with ui.column().classes("w-full h-full"):
                            ui.label("Assign Roles")
                    with ui.tab_panel(define_tab).classes(
                        "w-full h-full rounded-lg border border-gray-300"
                    ):
                        self.render_define_role_tab()
            with ui.column().classes("col-span-1 p-4"):
                self._render_org_chart()  # Replace ui.label with Mermaid chart

    def handle_new_role(self):
        """Handle click of New Role button"""
        # Change view to new role form
        self.define_role_view = "role_tab_new"
        # Refresh the view
        self.render_define_role_tab.refresh()

    def handle_edit_role(self):
        """Handle click of Edit button"""
        if len(self.selected_roles) == 1:  # Ensure exactly one role is selected
            selected_role = self.selected_roles[0]

            # Map the selected role to new_role_config
            self.new_role_config = RoleModel(
                role_id=selected_role.role_id,
                role_name=selected_role.role_name,
                role_description=selected_role.role_description,
                role_reports_to=selected_role.role_reports_to,
                role_reporting_team=selected_role.role_reporting_team,
                role_responsibilities=selected_role.role_responsibilities,
                role_displayed_in_org=selected_role.role_displayed_in_org,
                assigned_to=selected_role.assigned_to,
                created_on=selected_role.created_on,
                created_by=selected_role.created_by,
                updated_on=selected_role.updated_on,
                updated_by=selected_role.updated_by,
            )

            # Change view to edit mode
            self.define_role_view = RoleView.EDIT_VIEW.value

            # Refresh the view
            self.render_define_role_tab.refresh()
