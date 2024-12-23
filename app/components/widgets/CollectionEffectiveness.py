from nicegui import ui
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import json
from .WidgetFramework import WidgetFramework
from modules import ListManager
from utils.func import create_date


class CollectionEffectivenessWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)

        # Initialize list manager and get client mappings
        self.list_manager = ListManager()
        self.client_map = {
            str(item): name
            for item, name in self.list_manager.get_list("client_map").items()
        }

        self.status_groups = {
            "Active": ["ACT", "HLST", "NEW"],
            "Payment Plan": ["PCRD", "PACH", "PPA", "PPD"],
            "Promise": ["PRA", "PRB"],
            "Legal/Special": ["LEG", "DIS", "HLD"],
            "Closed": ["PID", "SIF", "CLO"],
            "Bankruptcy": ["CK7", "CK13", "BAN"],
            "Other": ["CRA", "DEC", "SKP", "RTP"],
        }

        # Verify data loaded from parent
        for dataset in self.required_datasets:
            df = self.data_store.get(dataset)
            if df is not None:
                print(f"{dataset} shape: {df.shape}")

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _get_client_name(self, client_number):
        """Helper to get client name from number with fallback"""
        return self.client_map.get(str(client_number), f"Client {client_number}")

    def _convert_date(self, row, prefix):
        """Convert date components using create_date function"""
        try:
            month = row[f"{prefix}_month"]
            day = row[f"{prefix}_day"]
            year = row[f"{prefix}_year"]

            # Skip if any component is None or 'None'
            if any(str(x).lower() == "none" or pd.isna(x) for x in [month, day, year]):
                return pd.NaT

            # Format date string directly with zero-padding
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            return pd.to_datetime(date_str)
        except Exception as e:
            return pd.NaT

    def _clean_payment_amount(self, amount):
        """Clean and convert payment amount to float"""
        try:
            if pd.isna(amount) or amount is None:
                return 0.0
            # Convert to string first
            amount_str = str(amount)
            # Remove all special characters except period
            amount_str = "".join(c for c in amount_str if c.isdigit() or c == ".")
            # Convert to float
            return float(amount_str) if amount_str else 0.0
        except Exception as e:
            print(f"Error cleaning payment amount: {str(e)}, value: {amount}")
            return 0.0

    def _clean_numeric(self, value):
        """Clean and convert numeric value, handling all edge cases"""
        try:
            if pd.isna(value) or value is None or str(value).lower() == "none":
                return "0"
            # Try to convert to float first
            float_val = float(value)
            # Convert to int and then string
            return str(int(float_val))
        except (ValueError, TypeError):
            return "0"

    def _calculate_metrics(self):
        """Calculate all metrics and cache them"""
        print("\n=== Starting metrics calculation ===")
        metrics = {}

        try:
            # Get and clean data
            contacts_df = self.get_contacts().copy()
            transactions_df = self.get_transactions().copy()

            # Clean numeric fields
            contacts_df["client_number"] = contacts_df["client_number"].apply(
                self._clean_numeric
            )
            contacts_df["file_number"] = contacts_df["file_number"].apply(
                self._clean_numeric
            )
            transactions_df["file_number"] = transactions_df["file_number"].apply(
                self._clean_numeric
            )

            # Clean payment amounts
            transactions_df["payment_amount"] = transactions_df["payment_amount"].apply(
                self._clean_payment_amount
            )

            # Convert and filter posted dates
            transactions_df["posted_date"] = transactions_df.apply(
                lambda x: self._convert_date(x, "posted_date"), axis=1
            )
            transactions_df = transactions_df.dropna(subset=["posted_date"])

            print(f"Transactions after posted_date filter: {len(transactions_df)}")

            # Convert payment dates
            transactions_df["payment_date"] = transactions_df.apply(
                lambda x: self._convert_date(x, "payment_date"), axis=1
            )

            # Process each client
            unique_clients = contacts_df["client_number"].dropna().unique()
            print(f"\nProcessing {len(unique_clients)} clients: {unique_clients}")

            for client in unique_clients:
                print(f"\n=== Processing client: {client} ===")
                client_metrics = self._calculate_client_metrics(
                    client, contacts_df, transactions_df
                )
                metrics[client] = client_metrics
                print(f"Completed metrics for client {client}")

            # Add timestamp
            metrics["last_modified"] = int(datetime.now().timestamp())

            # Update cache
            self.update_metric_cache(metrics)
            print("\nMetrics calculation completed")

        except Exception as e:
            print(f"Error in _calculate_metrics: {str(e)}")
            import traceback

            print(traceback.format_exc())

    def _calculate_client_metrics(self, client, contacts_df, transactions_df):
        """Calculate metrics for a specific client"""
        try:
            # Filter for client
            client_contacts = contacts_df[contacts_df["client_number"] == client]
            client_accounts = client_contacts["file_number"].unique()
            client_transactions = transactions_df[
                transactions_df["file_number"].isin(client_accounts)
            ]

            print(f"\nClient {client}:")
            print(f"Number of accounts: {len(client_accounts)}")
            print(f"Number of contacts: {len(client_contacts)}")
            print(f"Number of transactions: {len(client_transactions)}")
            print(f"Sample accounts: {client_accounts[:5]}")

            # Calculate strategy success
            print("\nCalculating strategy success...")
            strategy_success = self._calculate_strategy_success(
                client_contacts, client_transactions
            )
            print(f"Strategy success results: {json.dumps(strategy_success, indent=2)}")

            # Calculate status transitions
            print("\nCalculating status transitions...")
            status_transitions = self._calculate_status_transitions(client_contacts)
            print(f"Status transitions: {json.dumps(status_transitions, indent=2)}")

            # Calculate transaction metrics
            print("\nCalculating transaction metrics...")
            valid_payments = client_transactions[
                client_transactions["payment_amount"] > 0
            ]
            print(f"Valid payments: {len(valid_payments)}")
            print(f"Payment amounts: {valid_payments['payment_amount'].tolist()}")

            transaction_metrics = {
                "total_payments": len(valid_payments),
                "total_amount": float(valid_payments["payment_amount"].sum()),
                "unique_accounts": len(valid_payments["file_number"].unique()),
                "avg_payment": (
                    float(valid_payments["payment_amount"].mean())
                    if not valid_payments.empty
                    else 0.0
                ),
            }

            print(f"Transaction metrics: {json.dumps(transaction_metrics, indent=2)}")

            return {
                "strategy_success": strategy_success,
                "status_transitions": status_transitions,
                "transaction_metrics": transaction_metrics,
            }

        except Exception as e:
            print(f"Error in _calculate_client_metrics: {str(e)}")
            import traceback

            print(traceback.format_exc())
            return {
                "strategy_success": {},
                "status_transitions": {},
                "transaction_metrics": {
                    "total_payments": 0,
                    "total_amount": 0.0,
                    "unique_accounts": 0,
                    "avg_payment": 0.0,
                },
            }

    def _calculate_strategy_success(self, contacts_df, transactions_df):
        """Calculate success rates for different strategies"""
        try:
            success_rates = {}
            print("\n=== Strategy Success Calculation ===")

            # Filter for valid payment amounts first
            valid_transactions = transactions_df[
                transactions_df["payment_amount"] > 0
            ].copy()
            print(f"Valid transactions with payments: {len(valid_transactions)}")

            # Convert payment dates and filter invalid dates
            valid_transactions["payment_date"] = valid_transactions.apply(
                lambda x: self._convert_date(x, "payment_date"), axis=1
            )
            valid_transactions = valid_transactions.dropna(subset=["payment_date"])

            for status, status_list in self.status_groups.items():
                print(f"\nProcessing {status} group:")

                # Get accounts for this status
                status_contacts = contacts_df[
                    contacts_df["account_status"].isin(status_list)
                ]
                status_accounts = status_contacts["file_number"].unique()

                if len(status_accounts) == 0:
                    continue

                # Get payments for accounts in this status
                status_payments = valid_transactions[
                    valid_transactions["file_number"].isin(status_accounts)
                ]
                paying_accounts = status_payments["file_number"].unique()
                total_payment_amount = float(status_payments["payment_amount"].sum())

                success_rate = (
                    len(paying_accounts) / len(status_accounts)
                    if len(status_accounts) > 0
                    else 0.0
                )

                print(f"{status} metrics:")
                print(f"Total accounts: {len(status_accounts)}")
                print(f"Paying accounts: {len(paying_accounts)}")
                print(f"Total payments: ${total_payment_amount:,.2f}")
                print(f"Success rate: {success_rate:.2%}")

                success_rates[status] = {
                    "total_accounts": int(len(status_accounts)),
                    "paying_accounts": int(len(paying_accounts)),
                    "total_payment_amount": total_payment_amount,
                    "success_rate": float(success_rate),
                }

            return success_rates

        except Exception as e:
            print(f"Error in _calculate_strategy_success: {str(e)}")
            import traceback

            print(traceback.format_exc())
            return {}

    def _calculate_status_transitions(self, contacts_df):
        """Calculate status transition patterns"""
        transitions = defaultdict(int)
        sorted_contacts = contacts_df.sort_values(["file_number", "created_date"])

        for _, group in sorted_contacts.groupby("file_number"):
            statuses = group["account_status"].tolist()
            for i in range(len(statuses) - 1):
                transition_key = f"{statuses[i]}|{statuses[i + 1]}"
                transitions[transition_key] += 1

        return dict(transitions)

    def render(self):
        """Render the collection effectiveness dashboard"""
        metrics = self.get_cached()

        # Get unique clients from contacts data and handle None values
        contacts_df = self.get_contacts()
        contacts_df["client_number"] = contacts_df["client_number"].astype(str)
        client_numbers = contacts_df["client_number"].dropna().unique()
        client_numbers = [c.split(".")[0] for c in client_numbers if c != "nan"]
        client_numbers = sorted(client_numbers)

        selected_client = client_numbers[0] if client_numbers else None

        with ui.card().classes("w-full p-6"):
            ui.label("Collection Effectiveness Analysis").classes(
                "text-2xl font-bold mb-4"
            )

            # Add client selector with mapped names
            def on_select(e):
                nonlocal selected_client
                selected_client = e.value
                strategy_content.refresh()
                performance_content.refresh()
                patterns_content.refresh()

            ui.select(
                options={c: self._get_client_name(c) for c in client_numbers},
                value=selected_client,
                label="Select Client",
                on_change=on_select,
            ).classes("w-full mb-4")

            @ui.refreshable
            def strategy_content():
                if selected_client not in metrics:
                    ui.label("No data available for selected client").classes("text-lg")
                    return
                client_metrics = metrics[selected_client]
                self._render_strategy_effectiveness(client_metrics, selected_client)

            @ui.refreshable
            def performance_content():
                if selected_client not in metrics:
                    ui.label("No data available for selected client").classes("text-lg")
                    return
                client_metrics = metrics[selected_client]
                self._render_collection_performance(client_metrics, selected_client)

            @ui.refreshable
            def patterns_content():
                if selected_client not in metrics:
                    ui.label("No data available for selected client").classes("text-lg")
                    return
                client_metrics = metrics[selected_client]
                self._render_payment_patterns(client_metrics, selected_client)

            with ui.tabs().classes("w-full") as tabs:
                strategy_tab = ui.tab("Strategy Effectiveness")
                performance_tab = ui.tab("Collection Performance")
                patterns_tab = ui.tab("Payment Patterns")

            with ui.tab_panels(tabs, value=strategy_tab).classes("w-full mt-4"):
                with ui.tab_panel(strategy_tab):
                    strategy_content()
                with ui.tab_panel(performance_tab):
                    performance_content()
                with ui.tab_panel(patterns_tab):
                    patterns_content()

    def _render_strategy_effectiveness(self, client_metrics, selected_client):
        """Render strategy effectiveness analysis"""
        print("\n=== Rendering Strategy Effectiveness ===")
        if "strategy_success" not in client_metrics:
            print("No strategy_success in client_metrics")
            ui.label("No strategy data available").classes("text-lg")
            return

        strategy_data = []
        for status, metrics in client_metrics["strategy_success"].items():
            print(f"\nProcessing status: {status}")
            print(f"Metrics: {metrics}")

            if metrics["total_accounts"] > 0:
                strategy_data.append(
                    {
                        "status": status,
                        "total_accounts": metrics["total_accounts"],
                        "paying_accounts": metrics["paying_accounts"],
                        "total_amount": metrics["total_payment_amount"],
                        "success_rate": metrics["success_rate"] * 100,
                    }
                )

        if not strategy_data:
            print("No strategy data after processing")
            ui.label("No strategy data available").classes("text-lg")
            return

        print(f"\nFinal strategy data:")
        print(json.dumps(strategy_data, indent=2))

        df = pd.DataFrame(strategy_data)

        # Create chart
        chart_data = {
            "chart": {"type": "column"},
            "title": {"text": "Strategy Success Rates"},
            "xAxis": {"categories": df["status"].tolist()},
            "yAxis": [
                {
                    "title": {"text": "Count"},
                    "labels": {"format": "{value}"},
                },
                {
                    "title": {"text": "Success Rate"},
                    "labels": {"format": "{value}%"},
                    "opposite": True,
                },
            ],
            "series": [
                {
                    "name": "Total Accounts",
                    "type": "column",
                    "data": df["total_accounts"].tolist(),
                },
                {
                    "name": "Success Rate",
                    "type": "line",
                    "yAxis": 1,
                    "data": df["success_rate"].round(1).tolist(),
                },
            ],
        }

        ui.highchart(chart_data).classes("w-full h-64")

        # Add metrics cards
        with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
            for data in strategy_data:
                with ui.card().classes("p-4"):
                    ui.label(data["status"]).classes("text-lg font-bold mb-2")
                    with ui.column().classes("gap-2"):
                        ui.label(f"Total Accounts: {data['total_accounts']:,}")
                        ui.label(f"Paying Accounts: {data['paying_accounts']:,}")
                        ui.label(f"Total Payments: ${data['total_amount']:,.2f}")
                        ui.label(f"Success Rate: {data['success_rate']:.1f}%")

    def _render_collection_performance(self, client_metrics, selected_client):
        """Render collection performance analysis"""
        try:
            transactions_df = self.get_transactions().copy()
            contacts_df = self.get_contacts().copy()

            # Clean and prepare data
            contacts_df["client_number"] = contacts_df["client_number"].apply(
                self._clean_numeric
            )
            contacts_df["file_number"] = contacts_df["file_number"].apply(
                self._clean_numeric
            )
            transactions_df["file_number"] = transactions_df["file_number"].apply(
                self._clean_numeric
            )

            # Clean payment amounts
            transactions_df["payment_amount"] = transactions_df["payment_amount"].apply(
                self._clean_payment_amount
            )

            print("\nStarting collection performance calculation")
            print(f"Initial transactions: {len(transactions_df)}")

            # Get client accounts first
            client_accounts = contacts_df[
                contacts_df["client_number"] == str(selected_client)
            ]["file_number"].unique()
            print(f"Found {len(client_accounts)} client accounts")

            # Filter transactions first
            client_transactions = transactions_df[
                transactions_df["file_number"].isin(client_accounts)
            ]
            print(f"Client transactions: {len(client_transactions)}")

            # Filter for valid payments
            valid_payments = client_transactions[
                client_transactions["payment_amount"] > 0
            ].copy()
            print(f"Valid payments: {len(valid_payments)}")

            if valid_payments.empty:
                ui.label("No payment data available").classes("text-lg")
                return

            # Convert dates
            valid_payments["payment_date"] = valid_payments.apply(
                lambda x: self._convert_date(x, "payment_date"), axis=1
            )
            valid_payments = valid_payments.dropna(subset=["payment_date"])
            print(f"Payments after date filtering: {len(valid_payments)}")
            print(
                f"Sample payment dates: {valid_payments['payment_date'].head().tolist()}"
            )

            # Group by month
            valid_payments["month"] = pd.to_datetime(
                valid_payments["payment_date"]
            ).dt.strftime("%Y-%m")
            print(f"Unique months: {valid_payments['month'].unique().tolist()}")

            monthly_stats = (
                valid_payments.groupby("month")
                .agg(
                    {
                        "payment_amount": ["count", "sum", "mean"],
                        "file_number": "nunique",
                    }
                )
                .reset_index()
            )
            monthly_stats.columns = [
                "month",
                "payment_count",
                "total_amount",
                "avg_payment",
                "unique_accounts",
            ]
            monthly_stats = monthly_stats.sort_values("month")

            print("\nMonthly stats:")
            print(monthly_stats)

            # Create performance chart
            chart_data = {
                "chart": {"type": "column"},
                "title": {"text": "Monthly Collection Performance"},
                "xAxis": {
                    "categories": monthly_stats["month"].tolist(),
                    "labels": {"rotation": -45},
                },
                "yAxis": [
                    {
                        "title": {"text": "Amount ($)"},
                        "labels": {"format": "${value:,.0f}"},
                    },
                    {
                        "title": {"text": "Count"},
                        "opposite": True,
                    },
                ],
                "series": [
                    {
                        "name": "Total Collections",
                        "type": "column",
                        "yAxis": 0,
                        "data": monthly_stats["total_amount"].round(2).tolist(),
                    },
                    {
                        "name": "Active Accounts",
                        "type": "line",
                        "yAxis": 1,
                        "data": monthly_stats["unique_accounts"].tolist(),
                    },
                ],
            }

            ui.highchart(chart_data).classes("w-full h-64")

            # Add summary metrics
            with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                with ui.card().classes("p-4"):
                    ui.label("Overall Performance").classes("text-lg font-bold mb-2")
                    with ui.column().classes("gap-2"):
                        total_amount = valid_payments["payment_amount"].sum()
                        avg_payment = valid_payments["payment_amount"].mean()
                        unique_accounts = valid_payments["file_number"].nunique()

                        ui.label(f"Total Collections: ${total_amount:,.2f}")
                        ui.label(f"Total Payments: {len(valid_payments):,}")
                        ui.label(f"Unique Accounts: {unique_accounts:,}")
                        ui.label(f"Average Payment: ${avg_payment:,.2f}")

        except Exception as e:
            print(f"Error in collection performance: {str(e)}")
            import traceback

            print(traceback.format_exc())
            ui.label("Error processing collection performance data").classes("text-lg")

    def _render_payment_patterns(self, client_metrics, selected_client):
        """Render payment pattern analysis"""
        try:
            transactions_df = self.get_transactions().copy()
            contacts_df = self.get_contacts().copy()

            # Clean and prepare data
            contacts_df["client_number"] = contacts_df["client_number"].apply(
                self._clean_numeric
            )
            contacts_df["file_number"] = contacts_df["file_number"].apply(
                self._clean_numeric
            )
            transactions_df["file_number"] = transactions_df["file_number"].apply(
                self._clean_numeric
            )

            # Clean payment amounts
            transactions_df["payment_amount"] = transactions_df["payment_amount"].apply(
                self._clean_payment_amount
            )

            # Convert and filter posted dates
            transactions_df["posted_date"] = transactions_df.apply(
                lambda x: self._convert_date(x, "posted_date"), axis=1
            )
            transactions_df = transactions_df.dropna(subset=["posted_date"])

            # Get client accounts
            client_accounts = contacts_df[
                contacts_df["client_number"] == str(selected_client)
            ]["file_number"].unique()

            # Filter transactions
            client_transactions = transactions_df[
                transactions_df["file_number"].isin(client_accounts)
            ]
            valid_payments = client_transactions[
                client_transactions["payment_amount"] > 0
            ].copy()

            if valid_payments.empty:
                ui.label("No payment data available").classes("text-lg")
                return

            # Convert dates and calculate day of week
            valid_payments["payment_date"] = valid_payments.apply(
                lambda x: self._convert_date(x, "payment_date"), axis=1
            )
            valid_payments["day_of_week"] = pd.to_datetime(
                valid_payments["payment_date"]
            ).dt.dayofweek

            # Calculate daily stats
            day_names = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            daily_stats = (
                valid_payments.groupby("day_of_week")
                .agg(
                    {
                        "payment_amount": ["count", "sum", "mean"],
                    }
                )
                .reset_index()
            )
            daily_stats.columns = [
                "day_of_week",
                "payment_count",
                "total_amount",
                "avg_payment",
            ]

            # Create daily pattern chart
            chart_data = {
                "chart": {"type": "column"},
                "title": {"text": "Payment Patterns by Day of Week"},
                "xAxis": {
                    "categories": [
                        day_names[int(d)] for d in daily_stats["day_of_week"]
                    ],
                    "title": {"text": "Day of Week"},
                },
                "yAxis": [
                    {
                        "title": {"text": "Amount ($)"},
                        "labels": {"format": "${value:,.0f}"},
                    },
                    {
                        "title": {"text": "Number of Payments"},
                        "opposite": True,
                    },
                ],
                "series": [
                    {
                        "name": "Total Amount",
                        "type": "column",
                        "yAxis": 0,
                        "data": daily_stats["total_amount"].round(2).tolist(),
                    },
                    {
                        "name": "Payment Count",
                        "type": "line",
                        "yAxis": 1,
                        "data": daily_stats["payment_count"].tolist(),
                    },
                ],
            }

            ui.highchart(chart_data).classes("w-full h-64")

            # Add pattern analysis cards
            with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                # Payment Frequency
                with ui.card().classes("p-4"):
                    ui.label("Payment Frequency").classes("text-lg font-bold mb-2")
                    account_payments = valid_payments.groupby("file_number").size()
                    with ui.column().classes("gap-2"):
                        ui.label(
                            f"Single Payment Accounts: {len(account_payments[account_payments == 1]):,}"
                        )
                        ui.label(
                            f"Multiple Payment Accounts: {len(account_payments[account_payments > 1]):,}"
                        )
                        ui.label(
                            f"High Activity Accounts (5+): {len(account_payments[account_payments >= 5]):,}"
                        )
                        ui.label(
                            f"Max Payments per Account: {account_payments.max():,}"
                        )

                # Payment Size Patterns
                with ui.card().classes("p-4"):
                    ui.label("Payment Size Patterns").classes("text-lg font-bold mb-2")
                    with ui.column().classes("gap-2"):
                        percentiles = valid_payments["payment_amount"].quantile(
                            [0.25, 0.5, 0.75]
                        )
                        ui.label(f"25th Percentile: ${percentiles[0.25]:,.2f}")
                        ui.label(f"Median Payment: ${percentiles[0.5]:,.2f}")
                        ui.label(f"75th Percentile: ${percentiles[0.75]:,.2f}")
                        ui.label(
                            f"Payment Range: ${valid_payments['payment_amount'].min():,.2f} - "
                            f"${valid_payments['payment_amount'].max():,.2f}"
                        )

                # Time-based Patterns
                with ui.card().classes("p-4"):
                    ui.label("Time-based Patterns").classes("text-lg font-bold mb-2")
                    with ui.column().classes("gap-2"):
                        busiest_day = daily_stats.loc[
                            daily_stats["payment_count"].idxmax()
                        ]
                        busiest_day_name = day_names[int(busiest_day["day_of_week"])]
                        ui.label(f"Most Active Day: {busiest_day_name}")
                        ui.label(f"Payments: {int(busiest_day['payment_count']):,}")
                        ui.label(f"Average Amount: ${busiest_day['avg_payment']:,.2f}")

                        weekend_mask = valid_payments["day_of_week"].isin([5, 6])
                        weekend_count = len(valid_payments[weekend_mask])
                        weekday_count = len(valid_payments[~weekend_mask])
                        weekend_ratio = (
                            weekend_count / weekday_count if weekday_count > 0 else 0
                        )
                        ui.label(f"Weekend/Weekday Ratio: {weekend_ratio:.2f}")

        except Exception as e:
            print(f"Error in payment patterns: {str(e)}")
            ui.label("Error processing payment pattern data").classes("text-lg")


def create_collection_effectiveness_widget(
    widget_configuration: dict = None, force_refresh=False
):
    """Factory function to create a new CollectionEffectivenessWidget instance."""
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["accounts", "transactions", "contacts"],
            "company_id": "ALL",
            "widget_id": "wgt_collection_effectiveness",
            "force_refresh": force_refresh,
        }
    return CollectionEffectivenessWidget(widget_configuration)
