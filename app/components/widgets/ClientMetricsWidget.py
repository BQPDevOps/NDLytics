from nicegui import ui
import pandas as pd
import numpy as np
from datetime import datetime
from .WidgetFramework import WidgetFramework


class ClientMetricsWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)

        # Verify data loaded from parent
        for dataset in self.required_datasets:
            df = self.data_store.get(dataset)

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _safe_date_convert(self, row, prefix):
        """Safely convert date components to a datetime"""
        try:
            month = row[f"{prefix}_month"]
            day = row[f"{prefix}_day"]
            year = row[f"{prefix}_year"]

            if pd.isna(month) or pd.isna(day) or pd.isna(year):
                return pd.NaT

            # Convert float values to integers
            month = int(float(month))
            day = int(float(day))
            year = int(float(year))

            # Validate date components
            if month < 1 or month > 12 or day < 1 or day > 31 or year < 1900:
                return pd.NaT

            # Create date string directly
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            return pd.to_datetime(date_str)

        except Exception as e:
            print(f"Error converting date: {str(e)} for {prefix}")
            print(f"Values - Month: {month}, Day: {day}, Year: {year}")
            return pd.NaT

    def _calculate_metrics(self):
        """Calculate all metrics and cache them"""
        metrics = {}

        # Calculate client metrics
        client_metrics = self._calculate_client_metrics()
        metrics["client_metrics"] = client_metrics

        # Add timestamp
        metrics["last_modified"] = int(datetime.now().timestamp())

        # Update cache
        self.update_metric_cache(metrics)

    def _calculate_client_metrics(self):
        """Calculate aggregate performance metrics at client level"""
        accounts_df = self.get_accounts()
        accounts_df["listed_date"] = accounts_df.apply(
            lambda x: self._safe_date_convert(x, "listed_date"), axis=1
        )

        transactions_df = self.get_transactions()
        transactions_df["payment_date"] = transactions_df.apply(
            lambda x: self._safe_date_convert(x, "payment_date"), axis=1
        )

        clients = []
        for client_number in accounts_df["client_number"].unique():
            client_accounts = accounts_df[accounts_df["client_number"] == client_number]
            client_payments = transactions_df[
                transactions_df["file_number"].isin(client_accounts["file_number"])
            ]

            total_placements = len(client_accounts["listed_date"].unique())
            total_loaded = client_accounts["original_upb_loaded"].sum()
            total_accounts = len(client_accounts)
            total_collected = client_payments["payment_amount"].sum()
            paying_accounts = client_payments["file_number"].nunique()

            avg_liquidation = (
                (total_collected / total_loaded * 100) if total_loaded > 0 else 0
            )
            avg_activation = (
                (paying_accounts / total_accounts * 100) if total_accounts > 0 else 0
            )

            monthly_rates = []
            for placement_date in client_accounts["listed_date"].unique():
                if pd.isna(placement_date):
                    continue

                placement = client_accounts[
                    client_accounts["listed_date"] == placement_date
                ]
                placement_loaded = placement["original_upb_loaded"].sum()

                if placement_loaded > 0:
                    placement_collected = transactions_df[
                        transactions_df["file_number"].isin(placement["file_number"])
                    ]["payment_amount"].sum()
                    monthly_rates.append((placement_collected / placement_loaded) * 100)

            liquidation_std = np.std(monthly_rates) if monthly_rates else 0

            performance_trend = 0
            if len(monthly_rates) >= 2:
                recent_half = monthly_rates[len(monthly_rates) // 2 :]
                older_half = monthly_rates[: len(monthly_rates) // 2]
                performance_trend = (
                    np.mean(recent_half) - np.mean(older_half)
                    if recent_half and older_half
                    else 0
                )

            clients.append(
                {
                    "client_number": client_number,
                    "total_placements": total_placements,
                    "total_loaded": round(total_loaded, 2),
                    "total_collected": round(total_collected, 2),
                    "total_accounts": total_accounts,
                    "paying_accounts": paying_accounts,
                    "avg_liquidation": round(avg_liquidation, 2),
                    "avg_activation": round(avg_activation, 2),
                    "liquidation_std": round(liquidation_std, 2),
                    "performance_trend": round(performance_trend, 2),
                }
            )

        return clients

    def render(self):
        """Render the client metrics dashboard"""
        metrics = self.get_cached()

        with ui.card().classes("w-full p-6"):
            ui.label("Client Performance Metrics").classes("text-2xl font-bold mb-4")

            if "client_metrics" in metrics:
                client_metrics = pd.DataFrame(metrics["client_metrics"])

                # Create summary chart
                chart_data = {
                    "chart": {"type": "column"},
                    "title": {"text": "Client Portfolio Performance"},
                    "xAxis": {
                        "categories": client_metrics["client_number"].tolist(),
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
                            "data": client_metrics["total_loaded"].tolist(),
                        },
                        {
                            "name": "Liquidation Rate",
                            "type": "line",
                            "yAxis": 1,
                            "data": client_metrics["avg_liquidation"].tolist(),
                        },
                        {
                            "name": "Activation Rate",
                            "type": "line",
                            "yAxis": 1,
                            "data": client_metrics["avg_activation"].tolist(),
                        },
                    ],
                }

                ui.highchart(chart_data).classes("w-full h-64")

                # Add client metric cards
                with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                    for _, client in client_metrics.iterrows():
                        with ui.card().classes("p-4"):
                            ui.label(f"Client {client['client_number']}").classes(
                                "text-lg font-bold mb-2"
                            )
                            with ui.column().classes("gap-2"):
                                ui.label(f"Placements: {client['total_placements']}")
                                ui.label(
                                    f"Total Loaded: ${client['total_loaded']:,.2f}"
                                )
                                ui.label(
                                    f"Total Collected: ${client['total_collected']:,.2f}"
                                )
                                ui.label(f"Total Accounts: {client['total_accounts']}")
                                ui.label(
                                    f"Paying Accounts: {client['paying_accounts']}"
                                )
                                ui.label(
                                    f"Avg Liquidation: {client['avg_liquidation']:.1f}%"
                                )
                                ui.label(
                                    f"Avg Activation: {client['avg_activation']:.1f}%"
                                )
                                ui.label(
                                    f"Performance Trend: "
                                    f"{'↑' if client['performance_trend'] > 0 else '↓'} "
                                    f"{abs(client['performance_trend']):.1f}%"
                                )


def create_client_metrics_widget(
    widget_configuration: dict = None, force_refresh=False
):
    """Factory function to create a new ClientMetricsWidget instance."""
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["accounts", "transactions"],
            "company_id": "ALL",
            "widget_id": "wgt_client_metrics",
            "force_refresh": force_refresh,
        }
    return ClientMetricsWidget(widget_configuration)
