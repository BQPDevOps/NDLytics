from nicegui import ui
from pydantic import BaseModel, ValidationError
from typing import Optional, Callable, Dict, Any


class NavButtonModel(BaseModel):
    icon: str
    title: str
    color: str
    route: str
    current_route: str
    callback: Optional[Callable] = None


class NavButton:
    def __init__(self, **kwargs):
        app_item = NavButtonModel(**kwargs)

        self.icon = app_item.icon
        self.title = app_item.title
        self.color = app_item.color
        self.route = app_item.route
        self.current_route = app_item.current_route
        self.callback = app_item.callback
        self.render()

    def render(self):
        is_selected = self.current_route == self.route
        on_click_action = (
            self.callback if self.callback else lambda: ui.navigate.to(self.route)
        )
        with ui.card().tight().style(
            f"""
            display:flex;
            flex-direction:column;
            justify-content:center;
            align-items:center;
            min-height:5rem;
            min-width:5rem;
            height:5.5rem;
            width:100%;
            border-radius:10px;
            border: 3px solid rgba(255,255,255,0);
            cursor: pointer;
            transition: all 250ms ease-in-out;
            gap:0;
            margin:0;
            padding:0;
            background-color: #EBECF0;
            transform: scale(1);
            {
                "box-shadow: inset -4px -4px 6px -1px rgba(255,255,255,1), inset 2px 2px 8px -1px rgba(72,79,96,0.5);"
                if is_selected else
                "box-shadow: 8px 8px 12px -2px rgba(72,79,96,0.4), -6px -6px 12px -1px rgba(255,255,255,1);"
            }
            """
        ).on("click", on_click_action) as card:
            icon_color = "#00E5FF" if is_selected else "#006187"
            with ui.column().style(
                "display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;width:100%;"
            ):
                ui.icon(self.icon, size="md").style(f"color:{icon_color};")
            with ui.row().style(
                "width:100%;height:2rem;display:flex;justify-content:center;align-items:center;"
            ):
                ui.label(self.title).style(
                    "font-size:0.8rem;font-weight:semibold;color:rgb(120,120,120);"
                )
            if self.route != self.current_route:
                # Add hover effect using JavaScript
                card.on("mouseenter", lambda: card.style("transform: scale(1.05)"))
                card.on("mouseleave", lambda: card.style("transform: scale(1)"))


def create_nav_button(app_data: Dict[str, Any], current_route: str) -> NavButton:
    """
    Create an AppContainer after validating input data against AppItem model

    Args:
        app_data: Dictionary containing app properties
        current_route: Current route to pass to AppContainer

    Returns:
        AppContainer instance

    Raises:
        ValueError: If required non-optional fields are missing
    """
    # Add current_route to app_data
    app_data["current_route"] = current_route

    # Add defaults for optional fields if missing
    if "callback" not in app_data:
        app_data["callback"] = None

    try:
        # Validate against model
        NavButtonModel(**app_data)
    except ValidationError as e:
        missing_fields = [error["loc"][0] for error in e.errors()]
        required_fields = [field for field in missing_fields if field != "callback"]

        if required_fields:
            raise ValueError(f"Missing required fields: {', '.join(required_fields)}")

    # Create and return container
    return NavButton(**app_data)


__all__ = ["NavButtonModel", "NavButton", "create_nav_button"]
