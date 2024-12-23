from nicegui import ui
import pandas as pd
import numpy as np
from datetime import datetime
from .WidgetFramework import WidgetFramework
from modules.list_manager.ListManager import ListManager


class PlacementMetricsWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)

        # Initialize list manager and get client mappings
        self.list_manager = ListManager()
        self.client_map = {
            str(item): name
            for item, name in self.list_manager.get_list("client_map").items()
        }

        # Verify data loaded from parent
        for dataset in self.required_datasets:
            df = self.data_store.get(dataset)

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _get_client_name(self, client_number):
        """Helper to get client name from number with fallback"""
        return self.client_map.get(str(client_number), f"Client {client_number}")

    def render(self):
        """Render the placement metrics dashboard"""
        try:
            metrics = self.get_cached()

            with ui.card().classes("w-full p-6"):
                ui.label("Placement Performance Metrics").classes(
                    "text-2xl font-bold mb-4"
                )

                if (
                    "placement_metrics" not in metrics
                    or not metrics["placement_metrics"]
                ):
                    ui.label("No placement metrics available").classes("text-lg")
                    return

                placement_metrics = pd.DataFrame(metrics["placement_metrics"])

                if placement_metrics.empty:
                    ui.label("No placement data available").classes("text-lg")
                    return

                # Convert placement_date to datetime if it's a string
                if isinstance(placement_metrics["placement_date"].iloc[0], str):
                    placement_metrics["placement_date"] = pd.to_datetime(
                        placement_metrics["placement_date"]
                    )

                # Group placements by client
                grouped_placements = {}
                for placement in metrics["placement_metrics"]:
                    client_num = str(placement["client_number"])
                    if client_num not in grouped_placements:
                        grouped_placements[client_num] = []
                    grouped_placements[client_num].append(placement)

                # Sort placements within each client group by date
                for client_num in grouped_placements:
                    grouped_placements[client_num].sort(
                        key=lambda x: pd.to_datetime(x["placement_date"])
                    )

                # Sort clients by name
                sorted_clients = sorted(
                    grouped_placements.keys(), key=lambda x: self._get_client_name(x)
                )

                if not sorted_clients:
                    ui.label("No client data available").classes("text-lg")
                    return

                # Create summary chart with grouped data
                all_categories = []
                all_loaded = []
                all_liquidation = []
                all_activation = []

                for client_num in sorted_clients:
                    for placement in grouped_placements[client_num]:
                        all_categories.append(
                            f"{self._get_client_name(client_num)} ({pd.to_datetime(placement['placement_date']).strftime('%Y-%m')})"
                        )
                        all_loaded.append(placement["total_loaded"])
                        all_liquidation.append(placement["liquidation_rate"])
                        all_activation.append(placement["activation_rate"])

                chart_data = {
                    "chart": {"type": "column"},
                    "title": {"text": "Placement Performance Overview"},
                    "xAxis": {
                        "categories": all_categories,
                        "labels": {"rotation": -45},
                    },
                    "yAxis": [
                        {
                            "title": {"text": "Amount ($)"},
                            "labels": {"format": "${value:,.0f}"},
                        },
                        {
                            "title": {"text": "Rate (%)"},
                            "opposite": True,
                        },
                    ],
                    "series": [
                        {
                            "name": "Total Loaded",
                            "type": "column",
                            "yAxis": 0,
                            "data": all_loaded,
                        },
                        {
                            "name": "Liquidation Rate",
                            "type": "line",
                            "yAxis": 1,
                            "data": all_liquidation,
                        },
                        {
                            "name": "Activation Rate",
                            "type": "line",
                            "yAxis": 1,
                            "data": all_activation,
                        },
                    ],
                }

                try:
                    ui.highchart(chart_data).classes("w-full h-64")
                except Exception as e:
                    ui.label("Error rendering chart").classes("text-red-500")

                # Render placement cards grouped by client
                with ui.column().classes(
                    "w-full h-[36vh] border-light-blue-500 border-2 rounded-lg shadow-inset p-0.5rem"
                ):
                    with ui.scroll_area().style("width: 100%; height:100%;"):
                        for client_num in sorted_clients:
                            client_name = self._get_client_name(client_num)
                            with ui.card().classes("w-full p-2 mt-1"):
                                with ui.expansion(text=client_name).classes("w-full"):
                                    with ui.grid(columns=1).classes("w-full gap-6"):
                                        for placement in grouped_placements[client_num]:
                                            try:
                                                placement_date = pd.to_datetime(
                                                    placement["placement_date"]
                                                )
                                                with ui.expansion(
                                                    value=True,
                                                    text=f"Placement - {placement_date.strftime('%Y-%m')}",
                                                ).classes("w-full"):
                                                    with ui.card().classes(
                                                        "w-full p-4 border-light-blue-500 border-2 rounded-lg shadow-inset"
                                                    ):
                                                        ui.label(
                                                            f"Placement - {placement_date.strftime('%Y-%m')}"
                                                        ).classes(
                                                            "text-md font-bold mb-2"
                                                        )

                                                        with ui.grid(columns=3).classes(
                                                            "gap-4"
                                                        ):
                                                            # Basic metrics
                                                            with ui.column().classes(
                                                                "gap-1 flex-1"
                                                            ):
                                                                ui.label(
                                                                    "Basic Metrics"
                                                                ).classes("font-bold")

                                                                ui.label(
                                                                    f"Account Count: {placement['account_count']}"
                                                                )
                                                                ui.label(
                                                                    f"Paying Accounts: {placement['paying_accounts']}"
                                                                )

                                                            with ui.column().classes(
                                                                "gap-1 flex-1"
                                                            ):
                                                                ui.label(
                                                                    "Financial Metrics"
                                                                ).classes("font-bold")
                                                                ui.label(
                                                                    f"Total Loaded: ${placement['total_loaded']:,.2f}"
                                                                )
                                                                ui.label(
                                                                    f"Total Collected: ${placement['total_collected']:,.2f}"
                                                                )

                                                            # Performance metrics
                                                            with ui.column().classes(
                                                                "gap-1 flex-1"
                                                            ):
                                                                ui.label(
                                                                    "Performance Metrics"
                                                                ).classes("font-bold")
                                                                ui.label(
                                                                    f"Liquidation Rate: {placement['liquidation_rate']:.1f}%"
                                                                )
                                                                ui.label(
                                                                    f"Activation Rate: {placement['activation_rate']:.1f}%"
                                                                )

                                                        # Monthly collections chart
                                                        monthly_chart = {
                                                            "chart": {"type": "line"},
                                                            "title": {
                                                                "text": "Monthly Collections"
                                                            },
                                                            "xAxis": {
                                                                "categories": [
                                                                    f"Month {i+1}"
                                                                    for i in range(12)
                                                                ]
                                                            },
                                                            "yAxis": [
                                                                {
                                                                    "title": {
                                                                        "text": "Amount ($)"
                                                                    },
                                                                    "labels": {
                                                                        "format": "${value:,.0f}"
                                                                    },
                                                                },
                                                                {
                                                                    "title": {
                                                                        "text": "Velocity (%)"
                                                                    },
                                                                    "opposite": True,
                                                                },
                                                            ],
                                                            "series": [
                                                                {
                                                                    "name": "Collections",
                                                                    "data": placement[
                                                                        "monthly_collections"
                                                                    ],
                                                                },
                                                                {
                                                                    "name": "Velocity",
                                                                    "type": "line",
                                                                    "yAxis": 1,
                                                                    "data": placement[
                                                                        "collection_velocity"
                                                                    ],
                                                                },
                                                            ],
                                                        }
                                                        ui.highchart(
                                                            monthly_chart
                                                        ).classes("w-full h-48 mt-4")
                                            except Exception as e:
                                                ui.label(
                                                    "Error rendering placement card"
                                                ).classes("text-red-500")

        except Exception as e:
            ui.label("Error rendering widget").classes("text-red-500")


def create_placement_metrics_widget(
    widget_configuration: dict = None, force_refresh=False
):
    """Factory function to create a new PlacementMetricsWidget instance."""
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["accounts", "transactions"],
            "company_id": "ALL",
            "widget_id": "wgt_placement_metrics",
            "force_refresh": force_refresh,
        }
    return PlacementMetricsWidget(widget_configuration)
