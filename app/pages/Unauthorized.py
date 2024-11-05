from nicegui import ui
from utils.helpers import cognito_adapter


def unauthorized_page():
    with ui.column().classes("flex justify-center items-center h-screen w-full"):
        with ui.card().classes("w-1/3 p-8 shadow-lg mb-8 border-gray-200"):
            with ui.column().classes(
                "flex justify-center items-center w-full space-y-4"
            ):
                ui.label("Unauthorized Access").classes("text-2xl font-bold")
                ui.label(
                    "You do not have the required permissions to access this page."
                ).classes("text-center")
                ui.label(
                    "Please contact your site administrator for further assistance."
                ).classes("text-center")
                ui.button(
                    "Return to Dashboard", on_click=lambda: ui.navigate.to("/dashboard")
                ).classes("w-full bg-blue-500 text-white py-2 rounded")
                ui.button(
                    "Signout", on_click=lambda: cognito_adapter.signout()
                ).classes("w-full bg-blue-500 text-white py-2 rounded")
