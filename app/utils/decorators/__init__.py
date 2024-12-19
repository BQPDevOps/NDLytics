from config import config
from functools import wraps
from nicegui import ui, app
from middleware.cognito import CognitoMiddleware


def permission_required(permission):
    """
    Decorator to check if the user has a specific permission.
    Combines session verification and permission check.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            authenticator = CognitoMiddleware()
            authenticator.initialize_user()
            if not authenticator.is_authenticated():
                ui.notify("Please log in to access this page.", type="error")
                ui.navigate.to("/signin")
                return
            if not authenticator.has_permission(permission):
                ui.notify(
                    "You do not have the necessary permissions to access this page.",
                    type="error",
                )
                ui.navigate.to("/unauthorized")
                return

            # Update last_accessed timestamp
            username = app.storage.user.get("username")
            session_id = app.storage.user.get("session_id")
            authenticator.update_last_accessed(username, session_id)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def permission_required_within(permission):
    """
    Decorator to enforce that a user has a specific permission to perform an action within a page.
    Shows a notification if lacking permission.

    Usage:
        @permission_required_within('dashboard_edit')
        def edit_dashboard():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            authenticator = CognitoMiddleware()
            authenticator.initialize_user()

            if not authenticator.is_authenticated():
                ui.notify("Please log in to perform this action.", type="error")
                ui.navigate.to("/signin")
                return

            if not authenticator.has_permission(permission):
                ui.notify(
                    "You do not have the necessary permissions to perform this action.",
                    type="error",
                )
                return

            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["permission_required", "permission_required_within"]
