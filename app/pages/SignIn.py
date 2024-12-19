from nicegui import ui, app

from middleware.cognito import create_cognito_middleware
from modules import ThemeManager


class SignInPage:
    def __init__(self):
        self.cognito_adapter = create_cognito_middleware()
        self.show_sms_mfa = {"value": False}
        self.username_input = ""
        self.password_input = ""
        self.sms_mfa_input = {"value": ""}
        self.login_button = {"value": ""}
        self.show_login_btn = {"value": True}
        self.show_submit_code_btn = {"value": False}
        self.show_new_password = {"value": False}
        self.show_confirm_new_password = {"value": False}
        self.new_password_input = {"value": ""}
        self.confirm_new_password_input = {"value": ""}
        self.show_forgot_password = {"value": False}
        self.forgot_password_email = {"value": ""}
        self.forgot_password_code = {"value": ""}
        self.forgot_password_new_password = {"value": ""}
        self.forgot_password_step = {"value": 1}
        self.theme_manager = ThemeManager()
        self.show_phone_setup = {"value": False}
        self.phone_number_input = {"value": ""}
        self.show_verify_phone = {"value": False}
        self.phone_number_for_password_reset = {"value": ""}
        self.show_phone_for_password_reset = {"value": False}
        self.given_name_input = {"value": ""}
        self.family_name_input = {"value": ""}
        self.show_user_attributes = {"value": False}
        self.show_password_reset = {"value": False}
        self.attributes_submitted = {"value": False}

    def handle_enter_key(self, e):
        """Handle enter key press in input fields"""
        if e.args.get("key") == "Enter":
            if self.show_forgot_password["value"]:
                # Handle forgot password flow
                if self.forgot_password_step["value"] == 1:
                    self.send_verification_code()
                elif self.forgot_password_step["value"] == 2:
                    self.verify_code()
                elif self.forgot_password_step["value"] == 3:
                    self.reset_password()
            elif self.show_sms_mfa["value"]:
                self.handle_mfa(self.mfa_input.value)
            elif self.show_new_password["value"]:
                self.submit_new_password()
            elif self.show_user_attributes["value"]:
                self.submit_user_attributes()
            else:
                # Normal login flow
                self.handle_login(self.username_input, self.password_input)

    def render_signin_page(self):
        with ui.column().classes("flex justify-center items-center h-screen w-full"):
            with ui.row().classes("flex justify-center items-center w-1/3"):
                ui.image("static/images/branding/ndlytics_logo_light.svg").classes(
                    "w-2/3"
                )
            with ui.card().classes("w-1/3 p-8 mb-8").style(
                "border: 1px solid rgba(204,204,204,0.6);border-radius: 10px;box-shadow: 0 8px 18px rgba(0, 0, 0, 0.3);"
            ):
                with ui.column().classes(
                    "flex justify-center items-center w-full space-y-4"
                ):
                    ui.label("Sign In").classes("text-2xl font-bold")

                    # Bind visibility of username and password inputs
                    with ui.column().classes("w-full").bind_visibility_from(
                        self.show_forgot_password, "value", lambda v: not v
                    ):
                        self.username_input = (
                            ui.input(
                                label="Username",
                                placeholder="Enter your username",
                            )
                            .classes("w-full")
                            .bind_value_to(self, "username_input")
                            .on("keydown", self.handle_enter_key)
                        )

                        self.password_input = (
                            ui.input(
                                label="Password",
                                placeholder="Enter your password",
                                password=True,
                            )
                            .classes("w-full")
                            .bind_value_to(self, "password_input")
                            .on("keydown", self.handle_enter_key)
                        )

                    self.mfa_input = (
                        ui.input(
                            label="MFA Code",
                            placeholder="Enter your MFA code",
                        )
                        .classes("w-full")
                        .bind_visibility_from(self.show_sms_mfa, "value")
                        .on("keydown", self.handle_enter_key)
                    )

                    # Add phone input for password reset
                    self.phone_number_for_password_reset = (
                        ui.input(
                            label="Phone Number",
                            placeholder="Enter your phone number (e.g., +1234567890)",
                        )
                        .classes("w-full")
                        .bind_visibility_from(
                            self.show_phone_for_password_reset, "value"
                        )
                    )

                    # Add new password inputs
                    with ui.column().classes("w-full space-y-4").bind_visibility_from(
                        self.show_new_password, "value"
                    ):
                        ui.label("Set New Password").classes("text-lg font-bold")

                        self.new_password_input = ui.input(
                            label="New Password",
                            placeholder="Enter your new password",
                            password=True,
                        ).classes("w-full")

                        self.confirm_new_password_input = ui.input(
                            label="Confirm New Password",
                            placeholder="Confirm your new password",
                            password=True,
                        ).classes("w-full")

                        ui.button(
                            "Set Password", on_click=self.submit_new_password
                        ).classes("w-full bg-blue-500 text-white py-2 rounded")

                    ui.button(
                        "Login",
                        on_click=lambda: self.handle_login(
                            self.username_input, self.password_input
                        ),
                    ).classes(f"w-full text-white py-2 rounded").bind_visibility_from(
                        self.show_login_btn, "value"
                    )

                    # Replace the ui.link with a ui.button styled as a link
                    ui.button(
                        "Forgot Password?", on_click=self.show_forgot_password_form
                    ).style(
                        "background-color: transparent; color: #007bff; border: none; padding: 0; margin: 0; cursor: pointer; box-shadow: none;"
                    ).props(
                        "flat"
                    ).bind_visibility_from(
                        self.show_login_btn, "value"
                    )

                    # Forgot Password form
                    with ui.column().classes("w-full space-y-4").bind_visibility_from(
                        self.show_forgot_password, "value"
                    ):
                        self.forgot_password_email = (
                            ui.input(
                                label="Email",
                                placeholder="Enter your email",
                            )
                            .classes("w-full")
                            .bind_visibility_from(
                                self.forgot_password_step, "value", lambda v: v == 1
                            )
                            .on("keydown", self.handle_enter_key)
                        )
                        ui.button(
                            "Send Code", on_click=self.send_verification_code
                        ).classes(
                            "w-full bg-blue-500 text-white py-2 rounded"
                        ).bind_visibility_from(
                            self.forgot_password_step, "value", lambda v: v == 1
                        )

                        self.forgot_password_code = (
                            ui.input(
                                label="Verification Code",
                                placeholder="Enter verification code",
                            )
                            .classes("w-full")
                            .bind_visibility_from(
                                self.forgot_password_step, "value", lambda v: v == 2
                            )
                            .on("keydown", self.handle_enter_key)
                        )
                        ui.button("Verify Code", on_click=self.verify_code).classes(
                            "w-full bg-blue-500 text-white py-2 rounded"
                        ).bind_visibility_from(
                            self.forgot_password_step, "value", lambda v: v == 2
                        )

                        self.forgot_password_new_password = (
                            ui.input(
                                label="New Password",
                                placeholder="Enter new password",
                                password=True,
                            )
                            .classes("w-full")
                            .bind_visibility_from(
                                self.forgot_password_step, "value", lambda v: v == 3
                            )
                            .on("keydown", self.handle_enter_key)
                        )
                        ui.button(
                            "Reset Password", on_click=self.reset_password
                        ).classes(
                            "w-full bg-blue-500 text-white py-2 rounded"
                        ).bind_visibility_from(
                            self.forgot_password_step, "value", lambda v: v == 3
                        )

                        # Add "Back to Login" button
                        ui.button("Back to Login", on_click=self.back_to_login).classes(
                            "w-full bg-gray-300 text-gray-700 py-2 rounded mt-4"
                        )

                    ui.button(
                        "Submit Code",
                        on_click=lambda: self.handle_mfa(self.mfa_input.value),
                    ).classes(
                        "w-full bg-blue-500 text-white py-2 rounded"
                    ).bind_visibility_from(
                        self.show_submit_code_btn, "value"
                    )

                    # Add phone number setup form
                    with ui.column().classes("w-full space-y-4").bind_visibility_from(
                        self.show_phone_setup, "value"
                    ):
                        ui.label("Setup Phone Number for MFA").classes(
                            "text-lg font-bold"
                        )
                        ui.label("Required Format: +1234567890").classes(
                            "text-sm text-gray-500"
                        )
                        self.phone_number_input = ui.input(
                            label="Phone Number",
                            placeholder="Enter your phone number (e.g., +1234567890)",
                        ).classes("w-full")

                        ui.button(
                            "Set Up MFA", on_click=lambda: self.setup_phone_mfa()
                        ).classes("w-full bg-blue-500 text-white py-2 rounded")

                    # Add required user attributes for password reset
                    with ui.column().classes("w-full space-y-4").bind_visibility_from(
                        self.show_user_attributes, "value"
                    ):
                        ui.label("Additional Information Required").classes(
                            "text-lg font-bold"
                        )

                        self.given_name_input = ui.input(
                            label="First Name", placeholder="Enter your first name"
                        ).classes("w-full")

                        self.family_name_input = ui.input(
                            label="Last Name", placeholder="Enter your last name"
                        ).classes("w-full")

                        self.phone_number_for_password_reset = ui.input(
                            label="Phone Number",
                            placeholder="Enter your phone number (e.g., +1234567890)",
                        ).classes("w-full")

                        ui.button(
                            "Submit Information", on_click=self.submit_user_attributes
                        ).classes("w-full bg-blue-500 text-white py-2 rounded")

    def show_forgot_password_form(self):
        self.show_forgot_password["value"] = True
        self.show_login_btn["value"] = False
        self.forgot_password_step["value"] = 1

    def send_verification_code(self):
        email = self.forgot_password_email.value
        result = self.cognito_adapter.forgot_password(email)
        if result:
            ui.notify("Verification code sent to your email.")
            self.forgot_password_step["value"] = 2
        else:
            ui.notify("Failed to send verification code. Please try again.")

    def verify_code(self):
        code = self.forgot_password_code.value
        if code:
            # Here you might want to add some client-side validation
            self.forgot_password_step["value"] = 3
        else:
            ui.notify("Please enter the verification code.")

    def reset_password(self):
        email = self.forgot_password_email.value
        code = self.forgot_password_code.value
        new_password = self.forgot_password_new_password.value

        result = self.cognito_adapter.confirm_forgot_password(email, code, new_password)
        if result:
            ui.notify(
                "Password reset successful. Please sign in with your new password."
            )
            self.show_forgot_password["value"] = False
            self.show_login_btn["value"] = True
            self.forgot_password_step["value"] = 1
        else:
            ui.notify("Password reset failed. Please check your code and try again.")

    def handle_login(self, username, password):
        username = self.username_input
        password = self.password_input

        result = self.cognito_adapter.signin(username, password)

        if result == "NEW_PASSWORD_REQUIRED":
            # Clear any previously stored attributes
            if "user_attributes" in app.storage.user:
                del app.storage.user["user_attributes"]
            self.show_user_attributes["value"] = True
            self.show_login_btn["value"] = False
        elif result == "SMS_MFA":
            self.show_sms_mfa["value"] = True
            self.show_login_btn["value"] = False
            self.show_submit_code_btn["value"] = True
            # Add auto-focus to MFA input
            ui.run_javascript(
                "setTimeout(() => document.querySelector(\"input[placeholder='Enter your MFA code']\").focus(), 100)"
            )
        elif result:
            ui.navigate.to("/dashboard")
        else:
            ui.notify("Login failed. Please check your credentials.")

    def setup_phone_mfa(self):
        """Handle phone number setup for MFA"""
        phone_number = self.phone_number_input.value
        username = self.username_input

        if not phone_number:
            ui.notify("Please enter a valid phone number")
            return

        result = self.cognito_adapter.setup_mfa(username, phone_number)

        if result.get("success"):
            ui.notify("Phone number set up successfully. Please sign in again.")
            # Reset the form
            self.show_phone_setup["value"] = False
            self.show_login_btn["value"] = True
            self.phone_number_input.value = ""
        else:
            ui.notify(f"Failed to set up phone number: {result.get('error')}")

    def handle_mfa(self, mfa_code=None):
        result = self.cognito_adapter.handle_mfa(mfa_code)
        if result:
            ui.notify("Authentication successful!")
            ui.navigate.to("/dashboard")
        else:
            ui.notify("Invalid MFA code!")

    def handle_forgot_password(self):
        email = self.forgot_password_email.value
        code = self.forgot_password_code.value
        new_password = self.forgot_password_new_password.value

        if not code:
            # If no code is provided, initiate the password reset process
            result = self.cognito_adapter.forgot_password(email)
            print("HANDLE_FORGOT_PASSWORD: ", result)
            if result:
                ui.notify("Verification code sent to your email.")
            else:
                ui.notify("Failed to send verification code. Please try again.")
        else:
            # If code is provided, confirm the password reset
            result = self.cognito_adapter.confirm_forgot_password(
                email, code, new_password
            )
            if result:
                ui.notify(
                    "Password reset successful. Please sign in with your new password."
                )
                self.show_forgot_password["value"] = False
                self.show_login_btn["value"] = True
            else:
                ui.notify(
                    "Password reset failed. Please check your code and try again."
                )

    def back_to_login(self):
        self.show_forgot_password["value"] = False
        self.show_login_btn["value"] = True
        self.forgot_password_step["value"] = 1

        # Clear forgot password form inputs
        self.forgot_password_email.value = ""
        self.forgot_password_code.value = ""
        self.forgot_password_new_password.value = ""

    def submit_user_attributes(self):
        # Validate required fields
        if not self.given_name_input.value:
            ui.notify("Please enter your first name")
            return
        if not self.family_name_input.value:
            ui.notify("Please enter your last name")
            return
        if not self.phone_number_for_password_reset.value:
            ui.notify("Please enter your phone number")
            return

        user_attributes = {
            "given_name": self.given_name_input.value,
            "family_name": self.family_name_input.value,
            "phone_number": self.phone_number_for_password_reset.value,
        }

        result = self.cognito_adapter.update_user_attributes_for_new_user(
            self.username_input, user_attributes
        )

        if result.get("success"):
            self.show_user_attributes["value"] = False
            self.show_new_password["value"] = True
            self.show_confirm_new_password["value"] = True
            ui.notify(
                "Information submitted successfully. Please set your new password."
            )
        else:
            ui.notify(
                f"Failed to update information: {result.get('error', 'Unknown error')}"
            )

    def submit_new_password(self):
        if not self.new_password_input.value:
            ui.notify("Please enter a new password")
            return
        if not self.confirm_new_password_input.value:
            ui.notify("Please confirm your new password")
            return

        # Get stored attributes from app storage
        stored_attributes = app.storage.user.get("user_attributes", {})
        if not stored_attributes:
            ui.notify("Please provide your information first")
            return

        result = self.cognito_adapter.handle_new_password(
            self.new_password_input.value, self.confirm_new_password_input.value
        )

        if result.get("success"):
            if result["result"] == "SMS_MFA":
                # Hide all password-related fields
                self.show_password_reset["value"] = False
                self.show_new_password["value"] = False
                self.show_confirm_new_password["value"] = False
                self.show_user_attributes["value"] = False
                # Show MFA input
                self.show_sms_mfa["value"] = True
                self.show_submit_code_btn["value"] = True
                # Clear password fields
                self.password_input = ""
                self.new_password_input.value = ""
                self.confirm_new_password_input.value = ""
                ui.notify("Please enter the MFA code sent to your phone")
            else:
                ui.notify("Password reset successfully!")
                ui.navigate.to("/dashboard")
        else:
            ui.notify(f"Password reset failed: {result.get('error', 'Unknown error')}")


def signin_page():
    renderedPage = SignInPage()
    renderedPage.render_signin_page()
