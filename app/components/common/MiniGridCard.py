from nicegui import ui


class MiniGridCard:
    def __init__(
        self,
        grid_item_name,
        grid_item_icon,
        grid_item_icon_background_color="#FFFFFF",
        grid_item_icon_color="#000000",
        index=0,
        grid_item_path=None,
        grid_button_callback=None,
    ):
        self.grid_item_name = grid_item_name
        self.grid_item_icon = grid_item_icon
        self.grid_item_path = grid_item_path
        self.grid_item_icon_background_color = grid_item_icon_background_color
        self.grid_item_icon_color = grid_item_icon_color
        self.index = index
        self.grid_button_callback = grid_button_callback
        self.card = None

    def add_hover(self, _):
        """Add hover effect by updating the card's box-shadow."""
        self.card.style("box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.3);")

    def remove_hover(self, _):
        """Remove hover effect by restoring the card's original box-shadow."""
        self.card.style("box-shadow: 0 0 5px 0 rgba(0, 0, 0, 0.1);")

    def handle_click(self, _):
        if self.grid_button_callback:
            self.grid_button_callback()
        else:
            ui.navigate.to(self.grid_item_path)

    def render(self):
        # Create the card with inline CSS and set up the hover effect
        with ui.card().tight().style(
            """
            display:flex;
            height:10rem;
            width:8rem;
            border-radius:0.5rem;
            cursor:pointer;
            transition:all 0.3s;
            box-shadow: 0 0 5px 0 rgba(0, 0, 0, 0.1);
            border: 1px solid #D2D2D4;
            opacity: 0;
            transform: translateY(-20px);
            align-items:flex-start;
            gap:0.5rem;
            """
        ).on("click", self.handle_click).on("mouseover", self.add_hover).on(
            "mouseout", self.remove_hover
        ) as card:
            self.card = card
            with ui.row().style(
                "width:100%;height:60%;display:flex;align-items:center;justify-content:center;"
            ):
                with ui.card().style(
                    f"background-color:{self.grid_item_icon_background_color};display:flex;justify-content:center;align-items:center;width:80%;border: 1px solid #e2e8f0; border-radius: 0.5rem; box-shadow: 0 0 5px 0 rgba(0,0,0,0.1);"
                ):
                    ui.icon(
                        self.grid_item_icon, color=self.grid_item_icon_color
                    ).classes("text-2xl")
            with ui.row().style(
                "width:100%;display:flex;align-items:center;justify-content:center;"
            ):
                ui.label(self.grid_item_name).style(
                    "font-size:0.8rem;font-weight:bold;"
                )

            # Add the animation class after a short delay
            ui.timer(
                interval=0.5 * self.index,
                callback=lambda: card.classes("animate-card"),
                active=True,
            )
