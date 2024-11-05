from config import config

from services.framework import StorageManager
from utils.decorators import permission_required

from nicegui import ui

from pages import *


# Define the root page
@ui.page("/")
@permission_required("dashboard_view")
def root_page():
    ui.navigate.to("/dashboard")


# Define the dashboard page
@ui.page("/dashboard")
@permission_required("dashboard_view")
def endpoint_dashboard_page():
    storage = StorageManager()
    dashboard_page(storage)


@ui.page("/campaigns")
@permission_required("campaigns_view")
def endpoint_campaigns_page():
    storage = StorageManager()
    campaigns_page(storage)


@ui.page("/requests")
@permission_required("requests_view")
def endpoint_requests_page():
    storage = StorageManager()
    requests_page(storage)


@ui.page("/tickets")
@permission_required("tickets_view")
def endpoint_tickets_page():
    storage = StorageManager()
    tickets_page(storage)


@ui.page("/file-manager")
@permission_required("filemanager_view")
def endpoint_file_manager_page():
    storage = StorageManager()
    file_manager_page(storage)


@ui.page("/settings")
@permission_required("settings_view")
def endpoint_settings_page():
    storage = StorageManager()
    settings_page(storage)


@ui.page("/settings/ticket-system")
@permission_required("settings_view")
def endpoint_ticket_system_settings_page():
    storage = StorageManager()
    ticket_system_settings_page(storage)


# Define the signin page
@ui.page("/signin")
def render_signin_page():
    signin_page()


@ui.page("/unauthorized")
def render_unauthorized_page():
    unauthorized_page()


# Production
ui.run(
    storage_secret=config.app_storage_secret,
    reload=False,
    title="NDLytics",
    show=False,
    port=8000,  # env does not work for setting this
    host="0.0.0.0",
)
