from nicegui import ui
from modules import ThemeManager
from middleware.cognito import CognitoMiddleware


class UnauthorizedPage:
    def __init__(self):
        self.cognito_adapter = CognitoMiddleware()
        self.theme_manager = ThemeManager()

    def signout(self):
        """Handle signout action"""
        self.cognito_adapter.signout()

    def render_unauthorized_page(self):
        with ui.column().classes("flex justify-center items-center h-screen w-full"):
            with ui.card().classes("w-1/3 p-8").style(
                "border: 1px solid rgba(204,204,204,0.6);border-radius: 10px;box-shadow: 0 8px 18px rgba(0, 0, 0, 0.3);"
            ):
                with ui.column().classes(
                    "flex justify-center items-center w-full space-y-4"
                ):
                    ui.label("Unauthorized").classes("text-2xl font-bold")
                    ui.label("You do not have permission to access this page.").classes(
                        "text-gray-500"
                    )
                    ui.button(
                        "Signout",
                        on_click=self.signout,
                    ).classes("w-full bg-red-500 text-white py-2 rounded")


def unauthorized_page():
    renderedPage = UnauthorizedPage()
    renderedPage.render_unauthorized_page()
