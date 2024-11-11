from nicegui import ui


class GridCard:
    def __init__(
        self,
        grid_item_name,
        grid_item_description,
        grid_item_icon,
        grid_item_path,
        grid_item_icon_background_color="#FFFFFF",
        grid_item_icon_color="#000000",
        index=0,
    ):
        self.grid_item_name = grid_item_name
        self.grid_item_description = grid_item_description
        self.grid_item_icon = grid_item_icon
        self.grid_item_path = grid_item_path
        self.grid_item_icon_background_color = grid_item_icon_background_color
        self.grid_item_icon_color = grid_item_icon_color
        self.index = index
        self.card = None  # Reference to the card to update styles later

    def add_hover(self, _):
        """Add hover effect by updating the card's box-shadow."""
        self.card.style("box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.3);")

    def remove_hover(self, _):
        """Remove hover effect by restoring the card's original box-shadow."""
        self.card.style("box-shadow: 0 0 5px 0 rgba(0, 0, 0, 0.1);")

    def render(self):
        # Create the card with inline CSS and set up the hover effect
        with ui.card().style(
            """
            display:flex;
            height:18rem;
            width:14rem;
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
        ).on("click", lambda: ui.navigate.to(self.grid_item_path)).on(
            "mouseover", self.add_hover
        ).on(
            "mouseout", self.remove_hover
        ) as card:
            self.card = card
            with ui.row().style(
                "width:100%;height:60%;display:flex;align-items:center;justify-content:center;"
            ):
                with ui.card().style(
                    f"background-color:{self.grid_item_icon_background_color};display:flex;justify-content:center;align-items:center;width:70%;border: 1px solid #e2e8f0; border-radius: 0.5rem; box-shadow: 0 0 5px 0 rgba(0,0,0,0.1);"
                ):
                    ui.icon(
                        self.grid_item_icon, color=self.grid_item_icon_color
                    ).classes("text-5xl")
            with ui.row().style(
                "width:100%;height:40%;display:flex;align-items:center;justify-content:center;"
            ):
                with ui.column().style(
                    "display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;"
                ):
                    ui.label(self.grid_item_name).style(
                        "font-size:1.2rem;font-weight:bold;"
                    )
                    ui.label(self.grid_item_description).style(
                        "font-size:1rem;color:grey;"
                    )

            # Add the animation class after a short delay
            ui.timer(
                interval=0.5 * self.index,
                callback=lambda: card.classes("animate-card"),
                active=True,
            )
