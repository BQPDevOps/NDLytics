from nicegui import ui

from utils.helpers import cognito_adapter
from theme import ThemeManager


class SignInPage:
    def __init__(self):
        self.cognito_adapter = cognito_adapter()
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
        self.forgot_password_step = {"value": 1}  # 1: Email, 2: Code, 3: New Password
        self.theme_manager = ThemeManager()

    def render_signin_page(self):
        with ui.column().classes("flex justify-center items-center h-screen w-full"):
            with ui.row().classes("flex justify-center items-center w-1/3"):
                ui.image("static/images/branding/ndlytics_logo_light.svg").classes(
                    "w-1/3"
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
                        )

                        self.password_input = (
                            ui.input(
                                label="Password",
                                placeholder="Enter your password",
                                password=True,
                            )
                            .classes("w-full")
                            .bind_value_to(self, "password_input")
                        )

                    self.mfa_input = (
                        ui.input(
                            label="MFA Code",
                            placeholder="Enter your MFA code",
                        )
                        .classes("w-full")
                        .bind_visibility_from(self.show_sms_mfa, "value")
                    )

                    self.new_password_input = (
                        ui.input(
                            label="New Password",
                            placeholder="Enter your new password",
                            password=True,
                        )
                        .classes("w-full")
                        .bind_visibility_from(self.show_new_password, "value")
                    )

                    self.confirm_new_password_input = (
                        ui.input(
                            label="Confirm New Password",
                            placeholder="Confirm your new password",
                            password=True,
                        )
                        .classes("w-full")
                        .bind_visibility_from(self.show_confirm_new_password, "value")
                    )

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
                            ui.input(label="Email", placeholder="Enter your email")
                            .classes("w-full")
                            .bind_visibility_from(
                                self.forgot_password_step, "value", lambda v: v == 1
                            )
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
        # Manually trigger update to ensure values are up-to-date
        username = self.username_input
        password = self.password_input

        result = self.cognito_adapter.signin(username, password)
        if result == "SMS_MFA":
            self.show_sms_mfa["value"] = True
            self.show_login_btn["value"] = False
            self.show_submit_code_btn["value"] = True
        elif result == "NEW_PASSWORD_REQUIRED":
            self.show_new_password["value"] = True
            self.show_confirm_new_password["value"] = True
            self.show_login_btn["value"] = False
            self.show_submit_code_btn["value"] = True
        elif result:
            # Successfully signed in without MFA or new password required
            ui.navigate.to("/dashboard")

    def handle_mfa(self, mfa_code=None):
        if self.show_new_password["value"]:
            # Handle new password first
            result = self.cognito_adapter.handle_new_password(
                self.new_password_input.value,
                self.confirm_new_password_input.value,
            )
            if result:
                # Password reset was successful, redirect to dashboard
                ui.notify("Password reset successfully!")
                ui.navigate.to("/dashboard")
            else:
                ui.notify("Password reset failed!")
        else:
            # Handle MFA code
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


def signin_page():
    renderedPage = SignInPage()
    renderedPage.render_signin_page()
