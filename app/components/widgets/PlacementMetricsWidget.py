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
            print(
                f"Loaded {dataset} with shape: {df.shape if df is not None else 'None'}"
            )

        if self.is_recalc_needed() or self.force_refresh:
            print("Recalculating metrics...")
            self._calculate_metrics()
        else:
            print("Using cached metrics...")

    def _get_client_name(self, client_number):
        """Helper to get client name from number with fallback"""
        return self.client_map.get(str(client_number), f"Client {client_number}")

    def _safe_date_convert(self, row, date_column_prefix):
        """Convert separate date columns into a datetime object"""
        try:
            year = row.get(f"{date_column_prefix}_date_year", None)
            month = row.get(f"{date_column_prefix}_date_month", None)
            day = row.get(f"{date_column_prefix}_date_day", None)

            if pd.isna(year) or pd.isna(month) or pd.isna(day):
                print(f"Missing date component for {date_column_prefix}")
                return pd.NaT

            # Convert to integers and handle float values
            year = int(float(year))
            month = int(float(month))
            day = int(float(day))

            # Construct date string directly
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            date = pd.to_datetime(date_str)
            print(f"Converted to: {date}")
            return date

        except Exception as e:
            print(f"Date conversion error for {date_column_prefix}: {e}")
            print(f"Values - Year: {year}, Month: {month}, Day: {day}")
            return pd.NaT

    def _calculate_metrics(self):
        """Calculate placement metrics from accounts and transactions data"""
        print("\n=== Starting metric calculations ===")
        accounts_df = self.data_store.get("accounts")
        transactions_df = self.data_store.get("transactions")

        if accounts_df is None or transactions_df is None:
            print("Error: Missing required dataframes")
            self.update_metric_cache({"placement_metrics": []})
            return

        print(f"Processing accounts: {len(accounts_df)} rows")
        print(f"Processing transactions: {len(transactions_df)} rows")
        print("\nAccounts columns:", accounts_df.columns.tolist())
        print("Transactions columns:", transactions_df.columns.tolist())

        # Print sample of date columns
        print("\nSample account date columns:")
        date_cols = [col for col in accounts_df.columns if "date" in col.lower()]
        print(accounts_df[date_cols].head())

        print("\nSample transaction date columns:")
        date_cols = [col for col in transactions_df.columns if "date" in col.lower()]
        print(transactions_df[date_cols].head())

        # Convert date columns
        try:
            print("\nConverting placement dates...")
            accounts_df["placement_date"] = accounts_df.apply(
                lambda x: self._safe_date_convert(x, "listed"), axis=1
            )
            print("\nConverting payment dates...")
            transactions_df["payment_date"] = transactions_df.apply(
                lambda x: self._safe_date_convert(x, "payment"), axis=1
            )
        except Exception as e:
            print(f"Error during date conversion: {str(e)}")
            self.update_metric_cache({"placement_metrics": []})
            return

        print(f"\nValid placement dates: {accounts_df['placement_date'].notna().sum()}")
        print(f"Valid payment dates: {transactions_df['payment_date'].notna().sum()}")

        if accounts_df["placement_date"].notna().sum() == 0:
            print("No valid placement dates found")
            self.update_metric_cache({"placement_metrics": []})
            return

        # Group by month-year for placements
        accounts_df["placement_month"] = accounts_df["placement_date"].dt.strftime(
            "%Y-%m"
        )
        print(
            "\nUnique placement months:",
            accounts_df["placement_month"].unique().tolist(),
        )

        placements = []
        for client_number in accounts_df["client_number"].unique():
            print(f"\nProcessing client: {client_number}")
            client_accounts = accounts_df[accounts_df["client_number"] == client_number]
            print(f"Found {len(client_accounts)} accounts for client")

            for placement_month in client_accounts["placement_month"].unique():
                if pd.isna(placement_month):
                    continue

                placement = client_accounts[
                    client_accounts["placement_month"] == placement_month
                ]
                placement_id = f"{client_number}_{placement_month.replace('-', '')}"

                # Basic metrics
                account_count = len(placement)
                total_loaded = placement["original_upb_loaded"].sum()

                # Get transactions for this placement
                placement_transactions = transactions_df[
                    transactions_df["file_number"].isin(placement["file_number"])
                ]

                total_collected = placement_transactions["payment_amount"].sum()
                paying_accounts = placement_transactions["file_number"].nunique()

                print(
                    f"Placement {placement_id}: {account_count} accounts, ${total_loaded:,.2f} loaded, ${total_collected:,.2f} collected"
                )

                # Calculate rates
                liquidation_rate = (
                    (total_collected / total_loaded * 100) if total_loaded > 0 else 0
                )
                activation_rate = (
                    (paying_accounts / account_count * 100) if account_count > 0 else 0
                )

                # Calculate monthly collections
                monthly_collections = []
                collection_velocity = []

                placement_start = pd.to_datetime(placement_month)
                for month in range(12):
                    month_end = placement_start + pd.DateOffset(months=month + 1)
                    month_start = placement_start + pd.DateOffset(months=month)

                    month_payments = placement_transactions[
                        (placement_transactions["payment_date"] >= month_start)
                        & (placement_transactions["payment_date"] < month_end)
                    ]

                    month_collected = month_payments["payment_amount"].sum()
                    monthly_collections.append(month_collected)

                    # Calculate velocity (percentage of total collected this month)
                    velocity = (
                        (month_collected / total_loaded * 100)
                        if total_loaded > 0
                        else 0
                    )
                    collection_velocity.append(velocity)

                placements.append(
                    {
                        "placement_id": placement_id,
                        "client_number": client_number,
                        "placement_date": placement_month,
                        "total_loaded": round(total_loaded, 2),
                        "account_count": account_count,
                        "total_collected": round(total_collected, 2),
                        "paying_accounts": paying_accounts,
                        "liquidation_rate": round(liquidation_rate, 2),
                        "activation_rate": round(activation_rate, 2),
                        "monthly_collections": [
                            round(x, 2) for x in monthly_collections
                        ],
                        "collection_velocity": [
                            round(x, 2) for x in collection_velocity
                        ],
                    }
                )

        print(f"\nTotal placements processed: {len(placements)}")
        if not placements:
            print("No placements were processed")
            self.update_metric_cache({"placement_metrics": []})
            return

        print(
            "Sample placement data:", placements[0] if placements else "No placements"
        )
        self.update_metric_cache({"placement_metrics": placements})
        print("=== Metric calculations completed ===\n")

    def render(self):
        """Render the placement metrics dashboard"""
        try:
            metrics = self.get_cached()
            print("\n=== Starting render ===")
            print("Cached metrics keys:", metrics.keys() if metrics else "No metrics")

            with ui.card().classes("w-full p-6"):
                ui.label("Placement Performance Metrics").classes(
                    "text-2xl font-bold mb-4"
                )

                if not metrics:
                    print("No metrics found in cache")
                    ui.label("No placement metrics available").classes("text-lg")
                    return

                if (
                    "placement_metrics" not in metrics
                    or not metrics["placement_metrics"]
                ):
                    print("No placement_metrics in cache or empty list")
                    print("Available keys:", metrics.keys())
                    ui.label("No placement metrics available").classes("text-lg")
                    return

                placement_metrics = pd.DataFrame(metrics["placement_metrics"])
                print(f"Placement metrics shape: {placement_metrics.shape}")
                print("Placement metrics columns:", placement_metrics.columns.tolist())

                if placement_metrics.empty:
                    print("Placement metrics DataFrame is empty")
                    ui.label("No placement data available").classes("text-lg")
                    return

                # Group placements by client
                grouped_placements = {}
                for placement in metrics["placement_metrics"]:
                    client_num = str(placement["client_number"])
                    if client_num not in grouped_placements:
                        grouped_placements[client_num] = []
                    grouped_placements[client_num].append(placement)

                print(f"Found {len(grouped_placements)} clients")
                for client_num, placements in grouped_placements.items():
                    print(f"Client {client_num}: {len(placements)} placements")

                # Convert placement_date to datetime if it's a string
                if isinstance(placement_metrics["placement_date"].iloc[0], str):
                    placement_metrics["placement_date"] = pd.to_datetime(
                        placement_metrics["placement_date"]
                    )

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
