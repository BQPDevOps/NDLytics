from nicegui import ui, app
from config import config
from utils import permission_required
from modules.session_manager import SessionManager

from pages import *

import tracemalloc
import os

tracemalloc.start()


@ui.page("/")
@permission_required("dashboard_view")
def root():
    ui.navigate.to("/signin")


@ui.page("/signin")
def root_signing():
    signin_page()


@ui.page("/dashboard")
@permission_required("dashboard_view")
def root_dashboard():
    """Dashboard page route handler"""
    session_manager = SessionManager()
    return dashboard_page(session_manager)


@ui.page("/campaigns")
@permission_required("dashboard_view")
def root_campaigns():
    session_manager = SessionManager()
    return campaigns_page(session_manager)


@ui.page("/tasks")
@permission_required("dashboard_view")
def root_tasks():
    session_manager = SessionManager()
    return tasks_page(session_manager)


@ui.page("/goals")
@permission_required("dashboard_view")
def root_goals():
    session_manager = SessionManager()
    return goals_page(session_manager)


@ui.page("/settings")
@permission_required("dashboard_view")
def root_settings():
    session_manager = SessionManager()
    return settings_page(session_manager)


@ui.page("/unauthorized")
def root_unauthorized():
    unauthorized_page()


app.add_static_files("/static", "static")

ui.run(
    storage_secret=config.app_storage_secret,
    title="NDLytics",
    port=8000,
    host="0.0.0.0",
    show=False,
    reload=False,
)
