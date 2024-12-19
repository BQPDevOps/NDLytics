from nicegui import ui
from middleware.s3 import S3Middleware
from middleware.dynamo import DynamoMiddleware
from middleware.cognito import CognitoMiddleware
from config import config
from datetime import datetime
from modules import TokenManager, TokenType
from icecream import ic
from models import CompanyModel, UserProfileModel, UserModelExpanded, UserModel


class ManageUsersComponent:
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.cognito_middleware = CognitoMiddleware()
        self.s3_middleware = S3Middleware()
        self.users_dynamo_middleware = DynamoMiddleware(config.aws_users_table_name)
        self.companies_dynamo_middleware = DynamoMiddleware(
            config.aws_companies_table_name
        )
        self.user_id = None
        self.company_id = None
        self.user = None
        self.user_profile = None
        self.company_users = None
        self.selected_records = []
        self.user_checkboxes = []
        self._get_user()

    def _get_user(self):
        token = self.session_manager.get("id_token")
        token_manager = TokenManager(TokenType.ID, token)
        user = token_manager.get_decoded_token().dict()

        self.user_id = user.get("sub")
        self.company_id = self.cognito_middleware.get_all_custom_attributes(
            self.session_manager.get("username")
        ).get("custom:company_id")
        self.user = user

        # Get or create user profile
        self.user_profile = self.get_user_profile()

        # Get all users from same company and convert to UserModelExpanded instances
        cognito_users = self.cognito_middleware.get_users(company_id=self.company_id)
        company_users = [
            UserModelExpanded.from_cognito_user(user, self.company_id)
            for user in cognito_users
        ]

        # Get DynamoDB profiles for all users
        for user in company_users:
            try:
                key = {
                    "user_id": {"S": user.user_id},
                    "company_id": {"S": self.company_id},
                }
                user_record = self.users_dynamo_middleware.get_item(key)

                if user_record:
                    # Convert DynamoDB record to UserProfileModel and attach to user object
                    user_profile = UserProfileModel(
                        user_id=user_record["user_id"]["S"],
                        company_id=user_record["company_id"]["S"],
                        role=user_record["role"]["S"],
                        responsibilities=[
                            dict(r["M"]) for r in user_record["responsibilities"]["L"]
                        ],
                        updated_on=datetime.fromtimestamp(
                            int(user_record["updated_on"]["N"])
                        ),
                        updated_by=user_record["updated_by"]["S"],
                        created_on=datetime.fromtimestamp(
                            int(user_record["created_on"]["N"])
                        ),
                        created_by=user_record["created_by"]["S"],
                        goals=[dict(g["M"]) for g in user_record["goals"]["L"]],
                    )
                    user.profile = user_profile
                else:
                    # Create new profile if none exists
                    new_profile = UserProfileModel(
                        user_id=user.user_id,
                        company_id=self.company_id,
                        role="",
                        responsibilities=[],
                        updated_on=datetime.now(),
                        updated_by=self.user_id,
                        created_on=datetime.now(),
                        created_by=self.user_id,
                        goals=[],
                    )

                    # Convert to DynamoDB format and save
                    profile_item = {
                        "user_id": {"S": new_profile.user_id},
                        "company_id": {"S": new_profile.company_id},
                        "role": {"S": new_profile.role},
                        "responsibilities": {"L": []},
                        "updated_on": {
                            "N": str(int(new_profile.updated_on.timestamp()))
                        },
                        "updated_by": {"S": new_profile.updated_by},
                        "created_on": {
                            "N": str(int(new_profile.created_on.timestamp()))
                        },
                        "created_by": {"S": new_profile.created_by},
                        "goals": {"L": []},
                    }

                    self.users_dynamo_middleware.put_item(profile_item)
                    user.profile = new_profile

            except Exception as e:
                print(
                    f"Error getting/creating profile for user {user.user_id}: {str(e)}"
                )
                user.profile = None
        self.company_users = company_users

    def get_user_profile(self):
        try:
            # Try to get existing record
            key = {"user_id": {"S": self.user_id}, "company_id": {"S": self.company_id}}

            user_record = self.users_dynamo_middleware.get_item(key)

            if not user_record:
                # Create new profile if none exists
                new_profile = UserProfileModel(
                    user_id=self.user_id,
                    company_id=self.company_id,
                    role="",  # Default empty role
                    responsibilities=[],  # Empty responsibilities list
                    updated_on=datetime.now(),
                    updated_by=self.user_id,
                    created_on=datetime.now(),
                    created_by=self.user_id,
                    goals=[],  # Empty goals list
                )

                # Convert to DynamoDB format
                profile_item = {
                    "user_id": {"S": new_profile.user_id},
                    "company_id": {"S": new_profile.company_id},
                    "role": {"S": new_profile.role},
                    "responsibilities": {"L": []},
                    "updated_on": {"N": str(int(new_profile.updated_on.timestamp()))},
                    "updated_by": {"S": new_profile.updated_by},
                    "created_on": {"N": str(int(new_profile.created_on.timestamp()))},
                    "created_by": {"S": new_profile.created_by},
                    "goals": {"L": []},
                }

                # Save to DynamoDB
                self.users_dynamo_middleware.put_item(profile_item)
                return new_profile

            # Convert DynamoDB record to UserProfileModel
            return UserProfileModel(
                user_id=user_record["user_id"]["S"],
                company_id=user_record["company_id"]["S"],
                role=user_record["role"]["S"],
                responsibilities=[
                    dict(r["M"]) for r in user_record["responsibilities"]["L"]
                ],
                updated_on=datetime.fromtimestamp(int(user_record["updated_on"]["N"])),
                updated_by=user_record["updated_by"]["S"],
                created_on=datetime.fromtimestamp(int(user_record["created_on"]["N"])),
                created_by=user_record["created_by"]["S"],
                goals=[dict(g["M"]) for g in user_record["goals"]["L"]],
            )

        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return None

    def handle_select_all(self, e):
        if e.value:
            self.selected_records = self.company_users.copy()
        else:
            self.selected_records = []

        # Update all checkboxes in the list
        for checkbox in self.user_checkboxes:
            checkbox.value = e.value

        self._render_actions_bar.refresh()

    def handle_record_select(self, user, e):
        if e.value:
            if user not in self.selected_records:
                self.selected_records.append(user)
        else:
            if user in self.selected_records:
                self.selected_records.remove(user)

        self._render_actions_bar.refresh()

    def handle_new_user(self):
        # Create a class to hold the form data
        class NewUserForm:
            def __init__(self):
                self.first_name = ""
                self.last_name = ""
                self.email = ""
                self.phone = ""

        form = NewUserForm()

        dialog = ui.dialog().props("maximized")
        with dialog, ui.card().classes("w-full h-full"):
            with ui.grid(rows=3).classes("w-full h-full"):
                with ui.row().classes("row-span-2 w-full"):
                    with ui.grid(columns=4).classes("w-full h-full"):
                        with ui.column().classes("col-span-1"):
                            with ui.card().classes("w-full h-full rounded-lg flex-col"):
                                with ui.grid(rows=3).classes("w-full h-full"):
                                    with ui.row().classes(
                                        "row-span-1 items-center justify-center"
                                    ):
                                        with ui.avatar().classes("w-36 h-36"):
                                            ui.image(
                                                "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"
                                            ).classes(
                                                "object-cover rounded-full h-[90%] w-[90%]"
                                            )
                                    with ui.row().classes("row-span-2 w-full h-full"):
                                        with ui.column().classes(
                                            "w-full h-full pt-4 gap-0"
                                        ):
                                            with ui.row().classes(
                                                "w-full items-center justify-center"
                                            ):
                                                ui.label().bind_text_from(
                                                    form,
                                                    "first_name",
                                                    lambda x: f"{x or 'New'} {form.last_name}",
                                                ).style(
                                                    "font-size: 1.5rem; font-weight: bold;"
                                                )
                                            with ui.row().classes(
                                                "w-full items-center justify-center"
                                            ):
                                                ui.label("Role").style(
                                                    "font-size: 1.2rem; font-weight: 500; color: #666;"
                                                )
                                            with ui.column().classes(
                                                "w-full flex-grow items-center justify-center"
                                            ):
                                                with ui.row().classes(
                                                    "w-full items-center justify-center"
                                                ):
                                                    ui.button(
                                                        icon="key", text="Set Password"
                                                    ).classes("w-2/3 rounded-lg").props(
                                                        "outline"
                                                    )
                                                with ui.row().classes(
                                                    "w-full items-center justify-center"
                                                ):
                                                    ui.button(
                                                        icon="camera_alt",
                                                        text="Upload Photo",
                                                    ).classes("w-2/3 rounded-lg").props(
                                                        "outline"
                                                    )

                        with ui.column().classes("col-span-3 p-6"):
                            with ui.grid(columns=3).classes("w-full h-full"):
                                with ui.column().classes("col-span-1 w-full"):
                                    with ui.row().style(
                                        """
                                        display:flex;
                                        justify-content:flex-start;
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
                                        ui.label("User Details").style(
                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                    ui.input(
                                        label="First Name",
                                    ).classes(
                                        "w-full"
                                    ).props("outlined dense").bind_value(
                                        form, "first_name"
                                    )
                                    ui.input(
                                        label="Last Name",
                                    ).classes(
                                        "w-full"
                                    ).props("outlined dense").bind_value(
                                        form, "last_name"
                                    )
                                    ui.input(
                                        label="Email",
                                    ).classes("w-full").props(
                                        "outlined dense"
                                    ).bind_value(form, "email")
                                    ui.input(
                                        label="Phone",
                                    ).classes("w-full").props(
                                        "outlined dense"
                                    ).bind_value(form, "phone")
                                    ui.separator()
                                    with ui.row().classes(
                                        "w-full items-center justify-between"
                                    ):
                                        ui.label("Company Selection").style(
                                            "font-size:0.8rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        ui.button("New Company").props("size=sm")
                                    with ui.row().classes("w-full"):
                                        ui.select(
                                            options=[
                                                "Company 1",
                                                "Company 2",
                                                "Company 3",
                                            ],
                                        ).props("outlined dense").classes("w-full")
                                with ui.column().classes("col-span-2 w-full"):
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
                                        ui.label("Options").style(
                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        with ui.row().classes(
                                            "items-center justify-end"
                                        ):
                                            ui.button("Cancel").props("size=sm").style(
                                                "min-width: 130px;"
                                            )
                                            ui.button("Create User").props(
                                                "size=sm"
                                            ).style("min-width: 130px;")
                                    with ui.row().classes(
                                        "w-full h-full rounded-lg border border-gray-300 p-2"
                                    ):
                                        with ui.grid(columns=3).classes(
                                            "w-full h-full"
                                        ):
                                            with ui.column().classes("col-span-1"):
                                                with ui.row().classes(
                                                    "w-full items-center justify-between rounded-lg border border-gray-200 px-[1rem]"
                                                ):
                                                    ui.label("Send Invite").style(
                                                        "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                    )
                                                    ui.switch(
                                                        on_change=lambda e: print(
                                                            e.value
                                                        ),
                                                    )
                                                with ui.row().classes(
                                                    "w-full items-center justify-between rounded-lg border border-gray-200 px-[1rem]"
                                                ):
                                                    ui.label("Generate Password").style(
                                                        "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                    )
                                                    ui.switch(
                                                        on_change=lambda e: print(
                                                            e.value
                                                        ),
                                                    )
                                            with ui.column().classes(
                                                "col-span-2 border border-gray-300 rounded-lg p-4"
                                            ):
                                                with ui.tabs().classes(
                                                    "w-full"
                                                ) as tabs:
                                                    granular_permissions = ui.tab(
                                                        "Granular"
                                                    )
                                                    role_permissions = ui.tab("Role")
                                                with ui.tab_panels(
                                                    tabs, value=granular_permissions
                                                ).classes("flex-grow"):
                                                    with ui.tab_panel(
                                                        granular_permissions
                                                    ):
                                                        ui.label("Granular")
                                                    with ui.tab_panel(role_permissions):
                                                        ui.label("Role")

                with ui.row().classes("row-span-1 w-full").style(
                    "border-top: 1px solid #e0e0e0;"
                ):
                    with ui.grid(columns=2).classes("w-full h-full"):
                        with ui.column().classes("flex-grow p-2"):
                            with ui.card().classes("w-full h-full rounded-lg flex-col"):
                                with ui.row().classes(
                                    "w-full items-center justify-between"
                                ):
                                    ui.label("Goals").style(
                                        "font-size:0.8rem;font-weight:bold;color:#4A4A4A;"
                                    )
                                    ui.button("New Goal").props("size=sm")
                                ui.separator()
                        with ui.column().classes("flex-grow p-2"):
                            with ui.card().classes("w-full h-full rounded-lg flex-col"):
                                with ui.row().classes(
                                    "w-full items-center justify-between"
                                ):
                                    ui.label("Role & Responsibilities").style(
                                        "font-size:0.8rem;font-weight:bold;color:#4A4A4A;"
                                    )
                                    ui.button("New Role").props("size=sm")
                                ui.separator()

        dialog.open()

    def handle_edit_user(self):
        """Handle click of Edit button"""
        if len(self.selected_records) == 1:  # Ensure exactly one user is selected
            selected_user = self.selected_records[0]

            # Create a class to hold the form data
            class EditUserForm:
                def __init__(self):
                    self.first_name = selected_user.given_name
                    self.last_name = selected_user.family_name
                    self.email = selected_user.email
                    self.phone = selected_user.phone_number or ""

            form = EditUserForm()

            dialog = ui.dialog().props("maximized")
            with dialog, ui.card().classes("w-full h-full"):
                with ui.grid(rows=3).classes("w-full h-full"):
                    with ui.row().classes("row-span-2 w-full"):
                        with ui.grid(columns=4).classes("w-full h-full"):
                            with ui.column().classes("col-span-1"):
                                with ui.card().classes(
                                    "w-full h-full rounded-lg flex-col"
                                ):
                                    with ui.grid(rows=3).classes("w-full h-full"):
                                        with ui.row().classes(
                                            "row-span-1 items-center justify-center"
                                        ):
                                            with ui.avatar().classes("w-36 h-36"):
                                                ui.image(
                                                    "https://cdn-icons-png.flaticon.com/512/1077/1077114.png"
                                                ).classes(
                                                    "object-cover rounded-full h-[90%] w-[90%]"
                                                )
                                        with ui.row().classes(
                                            "row-span-2 w-full h-full"
                                        ):
                                            with ui.column().classes(
                                                "w-full h-full pt-4 gap-0"
                                            ):
                                                with ui.row().classes(
                                                    "w-full items-center justify-center"
                                                ):
                                                    ui.label().bind_text_from(
                                                        form,
                                                        "first_name",
                                                        lambda x: f"{x or selected_user.given_name} {form.last_name or selected_user.family_name}",
                                                    ).style(
                                                        "font-size: 1.5rem; font-weight: bold;"
                                                    )
                                                with ui.row().classes(
                                                    "w-full items-center justify-center"
                                                ):
                                                    ui.label(
                                                        selected_user.profile.role
                                                        if selected_user.profile
                                                        else "No Role"
                                                    ).style(
                                                        "font-size: 1.2rem; font-weight: 500; color: #666;"
                                                    )
                                                with ui.column().classes(
                                                    "w-full flex-grow items-center justify-center"
                                                ):
                                                    with ui.row().classes(
                                                        "w-full items-center justify-center"
                                                    ):
                                                        ui.button(
                                                            icon="key",
                                                            text="Reset Password",
                                                        ).classes(
                                                            "w-2/3 rounded-lg"
                                                        ).props(
                                                            "outline"
                                                        )
                                                    with ui.row().classes(
                                                        "w-full items-center justify-center"
                                                    ):
                                                        ui.button(
                                                            icon="camera_alt",
                                                            text="Upload Photo",
                                                        ).classes(
                                                            "w-2/3 rounded-lg"
                                                        ).props(
                                                            "outline"
                                                        )

                            with ui.column().classes("col-span-3 p-6"):
                                with ui.grid(columns=3).classes("w-full h-full"):
                                    with ui.column().classes("col-span-1 w-full"):
                                        with ui.row().style(
                                            """
                                            display:flex;
                                            justify-content:flex-start;
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
                                            ui.label("User Details").style(
                                                "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                            )
                                        ui.input(
                                            label="First Name",
                                            value=selected_user.given_name,
                                        ).classes("w-full").props(
                                            "outlined dense"
                                        ).bind_value(
                                            form, "first_name"
                                        )
                                        ui.input(
                                            label="Last Name",
                                            value=selected_user.family_name,
                                        ).classes("w-full").props(
                                            "outlined dense"
                                        ).bind_value(
                                            form, "last_name"
                                        )
                                        ui.input(
                                            label="Email", value=selected_user.email
                                        ).classes("w-full").props(
                                            "outlined dense"
                                        ).bind_value(
                                            form, "email"
                                        )
                                        ui.input(
                                            label="Phone",
                                            value=selected_user.phone_number,
                                        ).classes("w-full").props(
                                            "outlined dense"
                                        ).bind_value(
                                            form, "phone"
                                        )
                                        ui.separator()
                                        with ui.row().classes(
                                            "w-full items-center justify-between"
                                        ):
                                            ui.label("Company Selection").style(
                                                "font-size:0.8rem;font-weight:bold;color:#4A4A4A;"
                                            )
                                            ui.button("New Company").props("size=sm")
                                        with ui.row().classes("w-full"):
                                            # Create company options dictionary
                                            company_options = {
                                                selected_user.company_id: selected_user.company_id  # For now just show ID, can be enhanced later
                                            }

                                            # Then in the UI part:
                                            ui.select(
                                                options=company_options,
                                                value=selected_user.company_id,
                                            ).props("outlined dense").classes("w-full")
                                    with ui.column().classes("col-span-2 w-full"):
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
                                            ui.label("Options").style(
                                                "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                            )
                                            with ui.row().classes(
                                                "items-center justify-end"
                                            ):
                                                ui.button(
                                                    "Cancel", on_click=dialog.close
                                                ).props("size=sm").style(
                                                    "min-width: 130px;"
                                                )
                                                ui.button("Update User").props(
                                                    "size=sm"
                                                ).style("min-width: 130px;")
                                        with ui.row().classes(
                                            "w-full h-full rounded-lg border border-gray-300 p-2"
                                        ):
                                            with ui.grid(columns=3).classes(
                                                "w-full h-full"
                                            ):
                                                with ui.column().classes("col-span-1"):
                                                    with ui.row().classes(
                                                        "w-full items-center justify-between rounded-lg border border-gray-200 px-[1rem]"
                                                    ):
                                                        ui.label("Send Invite").style(
                                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                        )
                                                        ui.switch(
                                                            on_change=lambda e: print(
                                                                e.value
                                                            ),
                                                        )
                                                    with ui.row().classes(
                                                        "w-full items-center justify-between rounded-lg border border-gray-200 px-[1rem]"
                                                    ):
                                                        ui.label(
                                                            "Generate Password"
                                                        ).style(
                                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                                        )
                                                        ui.switch(
                                                            on_change=lambda e: print(
                                                                e.value
                                                            ),
                                                        )
                                                with ui.column().classes(
                                                    "col-span-2 border border-gray-300 rounded-lg p-4"
                                                ):
                                                    with ui.tabs().classes(
                                                        "w-full"
                                                    ) as tabs:
                                                        granular_permissions = ui.tab(
                                                            "Granular"
                                                        )
                                                        role_permissions = ui.tab(
                                                            "Role"
                                                        )
                                                    with ui.tab_panels(
                                                        tabs, value=granular_permissions
                                                    ).classes("flex-grow"):
                                                        with ui.tab_panel(
                                                            granular_permissions
                                                        ):
                                                            ui.label("Granular")
                                                        with ui.tab_panel(
                                                            role_permissions
                                                        ):
                                                            ui.label("Role")

                    with ui.row().classes("row-span-1 w-full").style(
                        "border-top: 1px solid #e0e0e0;"
                    ):
                        with ui.grid(columns=2).classes("w-full h-full"):
                            with ui.column().classes("flex-grow p-2"):
                                with ui.card().classes(
                                    "w-full h-full rounded-lg flex-col"
                                ):
                                    with ui.row().classes(
                                        "w-full items-center justify-between"
                                    ):
                                        ui.label("Goals").style(
                                            "font-size:0.8rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        ui.button("New Goal").props("size=sm")
                                    ui.separator()
                            with ui.column().classes("flex-grow p-2"):
                                with ui.card().classes(
                                    "w-full h-full rounded-lg flex-col"
                                ):
                                    with ui.row().classes(
                                        "w-full items-center justify-between"
                                    ):
                                        ui.label("Role & Responsibilities").style(
                                            "font-size:0.8rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        ui.button("New Role").props("size=sm")
                                    ui.separator()

            dialog.open()

    @ui.refreshable
    def _render_actions_bar(self):
        num_selected = len(self.selected_records)
        delete_text = f"({num_selected}) Delete" if num_selected > 0 else "Delete"
        edit_disabled = num_selected != 1

        with ui.column().classes("w-full px-4"):
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
                with ui.row().classes("h-full items-center"):
                    ui.button(icon="delete", text=delete_text).props(
                        f"size=sm {'disable' if num_selected == 0 else ''}"
                    ).style("min-width: 130px;").tooltip("Delete")
                    ui.button(
                        icon="edit",
                        text="Edit",
                        on_click=self.handle_edit_user,  # Add edit handler
                    ).props(f"size=sm {'disable' if edit_disabled else ''}").style(
                        "min-width: 130px;"
                    ).tooltip(
                        "Edit"
                    )
                with ui.row().classes("h-full items-center"):
                    ui.button(icon="add", on_click=self.handle_new_user).props(
                        "round size=sm"
                    ).tooltip("New User")

    def render(self):
        self.user_checkboxes = []  # Store checkbox references

        with ui.column().classes("w-full h-full p-2"):
            self._render_actions_bar()
            with ui.row().style("width:100%;height:100%;"):
                with ui.column().classes("w-full h-[76vh] gap-0"):
                    with ui.column().classes("w-full px-4"):
                        with ui.card().tight().classes("w-full"):
                            with ui.list().classes("w-full").props(
                                "bordered separator"
                            ):
                                with ui.item():
                                    with ui.item_section().props("side").style(
                                        "padding-right: 2rem; padding-left: 0.5rem; min-width: 100px;display:flex;justify-content:center;align-items:center;"
                                    ):
                                        ui.label("Select All").style(
                                            "font-size:0.7rem;font-weight:bold;color:#4A4A4A;white-space:nowrap;"
                                        )
                                        ui.checkbox(
                                            on_change=self.handle_select_all
                                        ).props("dense")
                                    with ui.row().classes(
                                        "w-full grid grid-cols-4 gap-4"
                                    ):
                                        ui.label("First Name").style(
                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        ui.label("Last Name").style(
                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        ui.label("Phone").style(
                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                        )
                                        ui.label("Role").style(
                                            "font-size:1rem;font-weight:bold;color:#4A4A4A;"
                                        )
                    with ui.scroll_area().classes("w-full h-[76vh]"):
                        with ui.list().props("bordered separator").classes(
                            "w-full h-full"
                        ):
                            for user in self.company_users:
                                with ui.item():
                                    with ui.item_section().props("side").style(
                                        "padding-right: 2rem; padding-left: 0.5rem; min-width: 100px;"
                                    ):
                                        checkbox = ui.checkbox(
                                            on_change=lambda e, u=user: self.handle_record_select(
                                                u, e
                                            )
                                        )
                                        self.user_checkboxes.append(checkbox)
                                    with ui.row().classes(
                                        "w-full grid grid-cols-4 gap-4"
                                    ):
                                        ui.label(user.given_name).style(
                                            "font-size:1rem;color:#4A4A4A;"
                                        )
                                        ui.label(user.family_name).style(
                                            "font-size:1rem;color:#4A4A4A;"
                                        )
                                        ui.label(user.phone_number or "N/A").style(
                                            "font-size:1rem;color:#4A4A4A;"
                                        )
                                        ui.label(
                                            user.profile.role
                                            if user.profile
                                            else "No Role"
                                        ).style("font-size:1rem;color:#4A4A4A;")
