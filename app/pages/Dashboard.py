# pages/dashboard.py
from components.shared import WidgetPage
from utils.lists import get_list


def dashboard_page(storage_manager):
    page = WidgetPage(
        page_title="Dashboard",
        page_route="/dashboard",
        page_description="Dashboard",
        tag_name="dashboard_page_config",
        storage_manager=storage_manager,
        creator_presets=get_list("dashboard_widgets"),
    )
    page.render()
