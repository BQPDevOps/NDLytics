from nicegui import ui, app
from config import config
from utils import permission_required
from modules.session_manager import SessionManager

from pages import *

import tracemalloc
import os
import atexit
import signal
import multiprocessing

tracemalloc.start()


def cleanup_resources():
    # Clean up multiprocessing resources
    for p in multiprocessing.active_children():
        p.terminate()
        p.join()  # Wait for process to terminate

    # Clean up semaphores
    try:
        from multiprocessing import resource_tracker

        if hasattr(resource_tracker, "_resource_tracker"):
            tracker = resource_tracker._resource_tracker
            if hasattr(tracker, "unregister"):
                for resource in tracker._resources:
                    try:
                        tracker.unregister(resource[0], resource[1])
                    except Exception:
                        pass
    except Exception:
        pass

    # Force garbage collection
    import gc

    gc.collect()


# Register cleanup handlers
atexit.register(cleanup_resources)
signal.signal(signal.SIGTERM, lambda *args: cleanup_resources())
signal.signal(signal.SIGINT, lambda *args: cleanup_resources())


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


@ui.page("/reports")
@permission_required("dashboard_view")
def root_reports():
    session_manager = SessionManager()
    return reports_page(session_manager)


@ui.page("/campaigns")
@permission_required("dashboard_view")
def root_campaigns():
    session_manager = SessionManager()
    return campaigns_page(session_manager)


@ui.page("/intelidoc")
@permission_required("dashboard_view")
def root_intelidoc():
    session_manager = SessionManager()
    return intelidoc_page(session_manager)


@ui.page("/resolutions")
@permission_required("dashboard_view")
def root_resolutions():
    session_manager = SessionManager()
    return resolutions_page(session_manager)


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


@ui.page("/tickets")
@permission_required("dashboard_view")
def root_tickets():
    session_manager = SessionManager()
    return tickets_page(session_manager)


@ui.page("/settings")
@permission_required("dashboard_view")
def root_settings():
    session_manager = SessionManager()
    return settings_page(session_manager)


@ui.page("/unauthorized")
def root_unauthorized():
    unauthorized_page()


import os

app.add_static_files("/static", os.path.join(os.path.dirname(__file__), "static"))

ui.run(
    storage_secret=config.app_storage_secret,
    title="NDLytics",
    port=8000,
    host="0.0.0.0",
    show=False,
    reload=True,
)
