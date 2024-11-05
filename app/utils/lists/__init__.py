from .user_permissions_list import user_permissions_list
from .user_roles_list import user_roles_list
from .page_routes_list import page_routes_list
from .lml_models_list import mlm_models_list
from .dashboard_widget_list import dashboard_widget_list
from .user_settings_route_list import user_settings_route_list


def get_list(list_name):
    lists = {
        "user_permissions": user_permissions_list,
        "user_roles": user_roles_list,
        "page_routes": page_routes_list,
        "mlm_models": mlm_models_list,
        "dashboard_widgets": dashboard_widget_list,
        "user_settings_routes": user_settings_route_list,
    }
    return lists.get(list_name)


__all__ = ["get_list"]
