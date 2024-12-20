from nicegui import ui
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import json
from .WidgetFramework import WidgetFramework
from modules import ListManager


class CollectionEffectivenessWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)

        self.status_groups = {
            "Active": ["ACT", "HLST", "NEW"],
            "Payment Plan": ["PCRD", "PACH", "PPA", "PPD"],
            "Promise": ["PRA", "PRB"],
            "Legal/Special": ["LEG", "DIS", "HLD"],
            "Closed": ["PID", "SIF", "CLO"],
            "Bankruptcy": ["CK7", "CK13", "BAN"],
            "Other": ["CRA", "DEC", "SKP", "RTP"],
        }

        if self.is_recalc_needed() or self.force_refresh:
            self._pull_required_data()
            self._calculate_metrics()

    def _calculate_metrics(self):
        metrics = {}

        # Calculate metrics for each client
        contacts_df = self.get_contacts()
        # Clean client numbers first
        contacts_df["client_number"] = contacts_df["client_number"].apply(
            lambda x: str(x).split(".")[0] if pd.notna(x) else None
        )

        # Debug logging

        for client in contacts_df["client_number"].dropna().unique():
            client_metrics = self._calculate_client_metrics(client)
            metrics[client] = client_metrics  # Store with original client number

        # Debug logging

        # Add timestamp
        metrics["last_modified"] = int(datetime.now().timestamp())

        # Update cache
        self.update_metric_cache(metrics)

    def _calculate_client_metrics(self, client):
        contacts_df = self.get_contacts()
        # Clean client numbers in contacts_df
        contacts_df["client_number"] = contacts_df["client_number"].apply(
            lambda x: str(x).split(".")[0] if pd.notna(x) else None
        )

        # Filter using clean client number
        client_accounts = contacts_df[contacts_df["client_number"] == str(client)][
            "file_number"
        ].unique()

        # Filter data for client
        client_contacts = contacts_df[contacts_df["file_number"].isin(client_accounts)]
        client_transactions = self.get_transactions()[
            self.get_transactions()["file_number"].isin(client_accounts)
        ]

        # Calculate metrics specific to this client
        strategy_success = self._calculate_strategy_success(
            client_contacts, client_transactions
        )
        status_transitions = self._calculate_status_transitions(client_contacts)

        # Store transaction data for performance and patterns tabs
        transaction_metrics = {
            "payment_data": client_transactions[
                client_transactions["payment_amount"] > 0
            ].to_dict(orient="records"),
            "total_payments": len(
                client_transactions[client_transactions["payment_amount"] > 0]
            ),
            "total_amount": float(client_transactions["payment_amount"].sum()),
            "unique_accounts": len(client_transactions["file_number"].unique()),
        }

        return {
            "strategy_success": strategy_success,
            "status_transitions": status_transitions,
            "transaction_metrics": transaction_metrics,
        }

    def _calculate_status_transitions(self, contacts_df):
        transitions = defaultdict(int)

        sorted_comments = contacts_df.sort_values("created_date")
        prev_status = {}

        for _, row in sorted_comments.iterrows():
            file_number = row["file_number"]
            current_status = row["account_status"]

            if file_number in prev_status:
                transition_key = f"{prev_status[file_number]}|{current_status}"
                transitions[transition_key] += 1

            prev_status[file_number] = current_status

        return dict(transitions)

    def _calculate_strategy_success(self, contacts_df, transactions_df):
        success_rates = {}

        valid_transactions = transactions_df[transactions_df["payment_amount"] > 0]

        all_statuses = contacts_df["account_status"].unique()

        for status in all_statuses:
            status_accounts = contacts_df[contacts_df["account_status"] == status][
                "file_number"
            ].unique()

            if len(status_accounts) == 0:
                continue

            status_dates = {}
            for account in status_accounts:
                status_date = contacts_df[
                    (contacts_df["file_number"] == account)
                    & (contacts_df["account_status"] == status)
                ]["created_date"].min()

                if pd.notna(status_date):
                    # Convert string to datetime if it's not already
                    if isinstance(status_date, str):
                        status_date = pd.to_datetime(status_date)
                    status_dates[account] = status_date

            payment_count = 0
            total_payment_amount = 0
            accounts_with_payments = set()

            for account, start_date in status_dates.items():
                end_date = start_date + timedelta(days=30)

                account_payments = valid_transactions[
                    (valid_transactions["file_number"] == account)
                    & (pd.to_datetime(valid_transactions["payment_date"]) >= start_date)
                    & (pd.to_datetime(valid_transactions["payment_date"]) <= end_date)
                ]

                if not account_payments.empty:
                    accounts_with_payments.add(account)
                    payment_count += len(account_payments)
                    total_payment_amount += account_payments["payment_amount"].sum()

            success_rate = (
                len(accounts_with_payments) / len(status_accounts)
                if len(status_accounts) > 0
                else 0
            )

            success_rates[status] = {
                "total_accounts": int(len(status_accounts)),
                "payments_within_30": int(payment_count),
                "total_payment_amount": float(total_payment_amount),
                "success_rate": float(success_rate),
            }

        return success_rates

    def render(self):
        metrics = self.get_cached()
        print("Cached metrics keys:", metrics.keys())  # Debug log

        # Get unique clients from contacts data and handle None values
        contacts_df = self.get_contacts()
        contacts_df["client_number"] = contacts_df["client_number"].astype(str)
        client_numbers = contacts_df["client_number"].dropna().unique()
        client_numbers = [c.split(".")[0] for c in client_numbers if c != "nan"]
        client_numbers = sorted(client_numbers)

        selected_client = client_numbers[0] if client_numbers else None

        # Initialize list manager and get client mappings
        list_manager = ListManager()
        client_map = list_manager.get_list("client_map")

        with ui.card().classes("w-full p-6"):
            ui.label("Collection Effectiveness Analysis").classes(
                "text-2xl font-bold mb-4"
            )

            # Add client selector with mapped names
            def on_select(e):
                nonlocal selected_client
                selected_client = e.value
                content.refresh(selected_client)

            ui.select(
                options={
                    c: client_map.get(
                        c, f"Client {c}"
                    )  # Use clean client number directly
                    for c in client_numbers
                },
                value=selected_client,
                label="Select Client",
                on_change=on_select,
            ).classes("w-full mb-4")

            with ui.tabs().classes("w-full") as tabs:
                strategy_tab = ui.tab("Strategy Effectiveness")
                performance_tab = ui.tab("Collection Performance")
                patterns_tab = ui.tab("Payment Patterns")

            @ui.refreshable
            def content(selected_client):
                with ui.tab_panels(tabs, value=strategy_tab).classes("w-full mt-4"):
                    with ui.tab_panel(strategy_tab):
                        self._render_strategy_effectiveness(metrics, selected_client)
                    with ui.tab_panel(performance_tab):
                        self._render_collection_performance(metrics, selected_client)
                    with ui.tab_panel(patterns_tab):
                        self._render_payment_patterns(metrics, selected_client)

            content(selected_client)

    def _render_strategy_effectiveness(self, metrics, selected_client):
        try:

            if selected_client in metrics:  # Try direct match first
                client_metrics = metrics[selected_client]
            else:
                with ui.card().classes("w-full p-4"):
                    ui.label(f"No data available for client {selected_client}").classes(
                        "text-lg"
                    )
                return

            if "strategy_success" in client_metrics:
                status_data = []
                for status, status_metrics in client_metrics[
                    "strategy_success"
                ].items():
                    if status_metrics["total_accounts"] > 0:
                        status_data.append(
                            {
                                "status": status,
                                "total_accounts": status_metrics["total_accounts"],
                                "payments_within_30": status_metrics[
                                    "payments_within_30"
                                ],
                                "total_payment_amount": status_metrics[
                                    "total_payment_amount"
                                ],
                                "success_rate": status_metrics["success_rate"] * 100,
                            }
                        )

                status_success = pd.DataFrame(status_data)
                if not status_success.empty:
                    status_success.set_index("status", inplace=True)

                    # Create chart data
                    chart_data = {
                        "chart": {"type": "column"},
                        "title": {"text": "Strategy Success Rates"},
                        "xAxis": {"categories": status_success.index.tolist()},
                        "yAxis": [
                            {
                                "title": {"text": "Number of Accounts"},
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
                                "yAxis": 0,
                                "data": status_success["total_accounts"].tolist(),
                            },
                            {
                                "name": "Success Rate",
                                "type": "line",
                                "yAxis": 1,
                                "data": status_success["success_rate"]
                                .round(1)
                                .tolist(),
                            },
                        ],
                    }

                    ui.highchart(chart_data).classes("w-full h-64")

                    # Add detailed metrics cards
                    with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                        for status_group, statuses in self.status_groups.items():
                            with ui.card().classes("p-4"):
                                ui.label(status_group).classes("text-lg font-bold mb-2")

                                group_metrics = {
                                    "total_accounts": 0,
                                    "payments_within_30": 0,
                                    "total_payment_amount": 0.0,
                                    "accounts_with_payments": 0,
                                }
                                print(f"Statuses for {status_group}: {statuses}")
                                for status in statuses:
                                    if status in client_metrics["strategy_success"]:
                                        status_metrics = client_metrics[
                                            "strategy_success"
                                        ][status]
                                        group_metrics[
                                            "total_accounts"
                                        ] += status_metrics["total_accounts"]
                                        group_metrics[
                                            "payments_within_30"
                                        ] += status_metrics["payments_within_30"]
                                        group_metrics[
                                            "total_payment_amount"
                                        ] += status_metrics["total_payment_amount"]
                                        group_metrics["accounts_with_payments"] += int(
                                            status_metrics["success_rate"]
                                            * status_metrics["total_accounts"]
                                        )

                                group_success_rate = (
                                    group_metrics["accounts_with_payments"]
                                    / group_metrics["total_accounts"]
                                    * 100
                                    if group_metrics["total_accounts"] > 0
                                    else 0.0
                                )

                                with ui.column().classes("gap-2"):
                                    ui.label(
                                        f"Accounts: {group_metrics['total_accounts']:,}"
                                    )
                                    ui.label(
                                        f"Number of Payments: {group_metrics['payments_within_30']:,}"
                                    )
                                    ui.label(
                                        f"Total Payment Amount: ${group_metrics['total_payment_amount']:,.2f}"
                                    )
                                    ui.label(f"Success Rate: {group_success_rate:.1f}%")

        except Exception as e:
            with ui.card().classes("w-full p-4"):
                ui.label(
                    "No data available for strategy effectiveness analysis"
                ).classes("text-lg")

    def _render_collection_performance(self, metrics, selected_client):
        try:

            if selected_client in metrics:
                client_metrics = metrics[selected_client]

                transactions_df = self.get_transactions()
                contacts_df = self.get_contacts()

                # Clean file numbers in both dataframes - remove decimal points
                contacts_df["file_number"] = contacts_df["file_number"].apply(
                    lambda x: str(x).split(".")[0] if pd.notna(x) else None
                )
                transactions_df["file_number"] = transactions_df["file_number"].apply(
                    lambda x: str(x).split(".")[0] if pd.notna(x) else None
                )

                # Clean client number and filter
                contacts_df["client_number"] = contacts_df["client_number"].apply(
                    lambda x: str(x).split(".")[0] if pd.notna(x) else None
                )

                # Filter for selected client
                client_accounts = contacts_df[
                    contacts_df["client_number"] == selected_client
                ]["file_number"].unique()

                # Filter transactions
                transactions_df = transactions_df[
                    transactions_df["file_number"].isin(client_accounts)
                ]

                if not transactions_df.empty:
                    valid_payments = transactions_df[
                        transactions_df["payment_amount"] > 0
                    ].copy()

                    if len(valid_payments) > 0:
                        # Monthly payment analysis
                        valid_payments["payment_year"] = valid_payments[
                            "payment_date_year"
                        ]
                        valid_payments["payment_month"] = valid_payments[
                            "payment_date_month"
                        ]
                        valid_payments["payment_month_str"] = valid_payments.apply(
                            lambda x: f"{x['payment_year']}-{x['payment_month']:02d}",
                            axis=1,
                        )

                        monthly_stats = (
                            valid_payments.groupby("payment_month_str")
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

                        # Create performance chart
                        performance_chart = {
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
                                {"title": {"text": "Count"}, "opposite": True},
                            ],
                            "series": [
                                {
                                    "name": "Total Collections",
                                    "type": "column",
                                    "yAxis": 0,
                                    "data": monthly_stats["total_amount"]
                                    .round(2)
                                    .tolist(),
                                },
                                {
                                    "name": "Active Accounts",
                                    "type": "line",
                                    "yAxis": 1,
                                    "data": monthly_stats["unique_accounts"].tolist(),
                                },
                            ],
                        }

                        ui.highchart(performance_chart).classes("w-full h-64")

                        # Add summary metrics
                        with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                            with ui.card().classes("p-4"):
                                ui.label("Overall Performance").classes(
                                    "text-lg font-bold mb-2"
                                )
                                total_amount = valid_payments["payment_amount"].sum()
                                avg_payment = valid_payments["payment_amount"].mean()
                                unique_accounts = valid_payments[
                                    "file_number"
                                ].nunique()

                                with ui.column().classes("gap-2"):
                                    ui.label(f"Total Collections: ${total_amount:,.2f}")
                                    ui.label(f"Total Payments: {len(valid_payments):,}")
                                    ui.label(f"Unique Accounts: {unique_accounts:,}")
                                    ui.label(f"Average Payment: ${avg_payment:,.2f}")
                    else:
                        with ui.card().classes("w-full p-4"):
                            ui.label("No valid payments found").classes("text-lg")
                else:
                    print("No transactions found after filtering")
                    with ui.card().classes("w-full p-4"):
                        ui.label("No transaction data available").classes("text-lg")
            else:
                print(f"Client {selected_client} not found in metrics")
                with ui.card().classes("w-full p-4"):
                    ui.label(f"No data available for client {selected_client}").classes(
                        "text-lg"
                    )

        except Exception as e:

            with ui.card().classes("w-full p-4"):
                ui.label("Error processing collection performance data").classes(
                    "text-lg"
                )

    def _render_payment_patterns(self, metrics, selected_client):
        try:

            if selected_client in metrics:
                client_metrics = metrics[selected_client]

                transactions_df = self.get_transactions()
                contacts_df = self.get_contacts()

                # Clean client number and filter
                contacts_df["client_number"] = contacts_df["client_number"].apply(
                    lambda x: str(x).split(".")[0] if pd.notna(x) else None
                )

                # Filter for selected client
                client_accounts = contacts_df[
                    contacts_df["client_number"] == selected_client
                ]["file_number"].unique()

                transactions_df = transactions_df[
                    transactions_df["file_number"].isin(client_accounts)
                ]

                if not transactions_df.empty:
                    valid_payments = transactions_df[
                        transactions_df["payment_amount"] > 0
                    ].copy()

                    if len(valid_payments) > 0:
                        # Day of Week Analysis
                        valid_payments["day_of_week"] = (
                            pd.to_numeric(valid_payments["payment_date_day"]) % 7
                        )
                        day_names = [
                            "Sunday",
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                        ]
                        daily_stats = (
                            valid_payments.groupby("day_of_week")
                            .agg({"payment_amount": ["count", "sum", "mean"]})
                            .reset_index()
                        )
                        daily_stats.columns = [
                            "day_of_week",
                            "payment_count",
                            "total_amount",
                            "avg_payment",
                        ]

                        # Create daily pattern chart
                        daily_chart = {
                            "chart": {"type": "column"},
                            "title": {"text": "Payment Patterns by Day of Week"},
                            "xAxis": {
                                "categories": [
                                    day_names[int(d)]
                                    for d in daily_stats["day_of_week"]
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
                                    "data": daily_stats["total_amount"]
                                    .round(2)
                                    .tolist(),
                                },
                                {
                                    "name": "Payment Count",
                                    "type": "line",
                                    "yAxis": 1,
                                    "data": daily_stats["payment_count"].tolist(),
                                },
                            ],
                        }

                        ui.highchart(daily_chart).classes("w-full h-64")

                        # Add pattern analysis cards
                        with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                            # Payment Frequency
                            with ui.card().classes("p-4"):
                                ui.label("Payment Frequency").classes(
                                    "text-lg font-bold mb-2"
                                )
                                account_payments = valid_payments.groupby(
                                    "file_number"
                                ).size()
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
                                ui.label("Payment Size Patterns").classes(
                                    "text-lg font-bold mb-2"
                                )
                                with ui.column().classes("gap-2"):
                                    percentiles = valid_payments[
                                        "payment_amount"
                                    ].quantile([0.25, 0.5, 0.75])
                                    ui.label(
                                        f"25th Percentile: ${percentiles[0.25]:,.2f}"
                                    )
                                    ui.label(
                                        f"Median Payment: ${percentiles[0.5]:,.2f}"
                                    )
                                    ui.label(
                                        f"75th Percentile: ${percentiles[0.75]:,.2f}"
                                    )
                                    ui.label(
                                        f"Payment Range: ${valid_payments['payment_amount'].min():,.2f} - ${valid_payments['payment_amount'].max():,.2f}"
                                    )

                            # Time-based Patterns
                            with ui.card().classes("p-4"):
                                ui.label("Time-based Patterns").classes(
                                    "text-lg font-bold mb-2"
                                )
                                with ui.column().classes("gap-2"):
                                    # Most active day
                                    busiest_day = daily_stats.loc[
                                        daily_stats["payment_count"].idxmax()
                                    ]
                                    busiest_day_name = day_names[
                                        int(busiest_day["day_of_week"])
                                    ]
                                    ui.label(f"Most Active Day: {busiest_day_name}")
                                    ui.label(
                                        f"Payments: {int(busiest_day['payment_count']):,}"
                                    )
                                    ui.label(
                                        f"Average Amount: ${busiest_day['avg_payment']:,.2f}"
                                    )

                                    # Week vs Weekend
                                    weekend_mask = valid_payments["day_of_week"].isin(
                                        [0, 6]
                                    )
                                    weekend_count = len(valid_payments[weekend_mask])
                                    weekday_count = len(valid_payments[~weekend_mask])
                                    ui.label(
                                        f"Weekend/Weekday Ratio: {weekend_count/weekday_count:.2f}"
                                    )
                    else:
                        with ui.card().classes("w-full p-4"):
                            ui.label("No valid payments found").classes("text-lg")
                else:
                    print("No transactions found after filtering")
                    with ui.card().classes("w-full p-4"):
                        ui.label("No transaction data available").classes("text-lg")
            else:
                print(f"Client {selected_client} not found in metrics")
                with ui.card().classes("w-full p-4"):
                    ui.label(f"No data available for client {selected_client}").classes(
                        "text-lg"
                    )

        except Exception as e:
            print(f"Error rendering payment patterns: {str(e)}")
            import traceback

            print(traceback.format_exc())
            with ui.card().classes("w-full p-4"):
                ui.label("Error processing payment pattern data").classes("text-lg")

    def is_widget_cached(self):
        cache = self._pull_metric_cache()
        if self.widget_id not in cache:
            key = {"company_id": {"S": self.company_id}}
            update_expression = (
                "SET metric_cache = if_not_exists(metric_cache, :empty_map)"
            )
            expression_values = {":empty_map": {"M": {self.widget_id: {"M": {}}}}}

            self.dynamo_client.update_item(key, update_expression, expression_values)
            return {}
        return cache.get(self.widget_id, {})

    def get_cached(self):
        """Override get_cached to handle force refresh"""
        if self.force_refresh:
            self._pull_required_data()
            self._calculate_metrics()
            return super().get_cached()

        return super().get_cached()

    def _render_placement_analysis(self, metrics):
        if "placement_metrics" not in metrics:
            with ui.card().classes("w-full p-4"):
                ui.label("No placement metrics available").classes("text-lg")
                return

        # Get unique clients from the data
        client_numbers = sorted(set(self.processed_accounts["client_number"]))
        selected_client = client_numbers[0] if client_numbers else None

        @ui.refreshable
        def placement_content(selected_client_number):
            # Filter data for selected client
            client_accounts = self.processed_accounts[
                self.processed_accounts["client_number"] == selected_client_number
            ]
            client_transactions = self.processed_transactions[
                self.processed_transactions["file_number"].isin(
                    client_accounts["file_number"]
                )
            ]

            # Create performance chart for selected client
            performance_chart = {
                "chart": {"type": "column"},
                "title": {
                    "text": f"Collection Performance - Client {selected_client_number}"
                },
                "xAxis": {
                    "categories": [
                        "Month 1",
                        "Month 2",
                        "Month 3",
                        "Month 4",
                        "Month 5",
                        "Month 6",
                    ]
                },
                "yAxis": [
                    {
                        "title": {"text": "Amount ($)"},
                        "labels": {"format": "${value:,.0f}"},
                    },
                    {
                        "title": {"text": "Success Rate (%)"},
                        "opposite": True,
                    },
                ],
                "series": [
                    {
                        "name": "Collections",
                        "type": "column",
                        "data": monthly_collections[:6],  # Show first 6 months
                    },
                    {
                        "name": "Success Rate",
                        "type": "line",
                        "yAxis": 1,
                        "data": success_rates[:6],  # Show first 6 months
                    },
                ],
            }

            ui.highchart(performance_chart).classes("w-full h-64")

            # Add client metrics cards
            with ui.grid(columns=2).classes("w-full gap-6 mt-6"):
                # Performance Metrics Card
                with ui.card().classes("p-4"):
                    ui.label("Performance Metrics").classes("text-lg font-bold mb-2")
                    with ui.column().classes("gap-2"):
                        ui.label(f"Total Accounts: {len(client_accounts):,}")
                        ui.label(
                            f"Active Accounts: {len(client_accounts[client_accounts['account_status'].isin(self.status_groups['Active'])]):,}"
                        )
                        ui.label(
                            f"Total Collections: ${client_transactions['payment_amount'].sum():,.2f}"
                        )
                        success_rate = (
                            len(client_transactions["file_number"].unique())
                            / len(client_accounts)
                            * 100
                        )
                        ui.label(f"Overall Success Rate: {success_rate:.1f}%")

                # Status Distribution Card
                with ui.card().classes("p-4"):
                    ui.label("Status Distribution").classes("text-lg font-bold mb-2")
                    with ui.column().classes("gap-2"):
                        for group_name, statuses in self.status_groups.items():
                            count = len(
                                client_accounts[
                                    client_accounts["account_status"].isin(statuses)
                                ]
                            )
                            percentage = (
                                count / len(client_accounts) * 100
                                if len(client_accounts) > 0
                                else 0
                            )
                            ui.label(f"{group_name}: {count:,} ({percentage:.1f}%)")

        # Create client selector
        def on_select(e):
            nonlocal selected_client
            selected_client = e.value
            placement_content.refresh(selected_client)

        ui.select(
            options={str(c): f"Client {c}" for c in client_numbers},
            value=str(selected_client) if selected_client else None,
            label="Select Client",
            on_change=on_select,
        ).classes("w-full mb-4")

        if selected_client:
            placement_content(selected_client)


def create_collection_effectiveness_widget(
    widget_configuration: dict = None, force_refresh=False
):
    """
    Factory function to create a new CollectionEffectivenessWidget instance.

    Args:
        widget_configuration (dict, optional): Configuration dictionary for the widget.
            If not provided, uses default configuration.
        force_refresh (bool, optional): Force refresh of data regardless of cache state.

    Returns:
        CollectionEffectivenessWidget: A configured widget instance ready for rendering
    """
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["accounts", "transactions", "contacts"],
            "company_id": "ALL",
            "widget_id": "wgt_collection_effectiveness",
            "force_refresh": force_refresh,
        }
    return CollectionEffectivenessWidget(widget_configuration)
