from nicegui import ui
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import json
from .WidgetFramework import WidgetFramework


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

        # Calculate metrics for each status group
        for group_name, statuses in self.status_groups.items():
            prefix = group_name.lower().replace(" ", "_")
            group_metrics = self._calculate_group_metrics(statuses)
            metrics.update(
                {
                    f"{prefix}_accounts": group_metrics["total_accounts"],
                    f"{prefix}_payments": group_metrics["payments"],
                    f"{prefix}_success_rate": group_metrics["success_rate"],
                }
            )

        # Calculate status transitions
        transitions = self._calculate_status_transitions()
        metrics["status_transitions"] = transitions

        # Calculate strategy success
        metrics["strategy_success"] = self._calculate_strategy_success()

        # Add timestamp
        metrics["last_modified"] = int(datetime.now().timestamp())

        # Update cache
        self.update_metric_cache(metrics)

    def _calculate_group_metrics(self, statuses):
        contacts_df = self.get_contacts()
        transactions_df = self.get_transactions()

        accounts_in_status = contacts_df[contacts_df["account_status"].isin(statuses)][
            "file_number"
        ].unique()

        if len(accounts_in_status) == 0:
            return {"total_accounts": 0, "payments": 0, "success_rate": 0}

        account_payments = transactions_df[
            transactions_df["file_number"].isin(accounts_in_status)
        ]

        total_payments = account_payments["payment_amount"].sum()
        accounts_with_payments = account_payments[
            account_payments["payment_amount"] > 0
        ]["file_number"].nunique()

        success_rate = (
            accounts_with_payments / len(accounts_in_status)
            if len(accounts_in_status) > 0
            else 0
        )

        return {
            "total_accounts": len(accounts_in_status),
            "payments": float(total_payments),
            "success_rate": float(success_rate),
        }

    def _calculate_status_transitions(self):
        contacts_df = self.get_contacts()
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

    def _calculate_strategy_success(self):
        contacts_df = self.get_contacts()
        transactions_df = self.get_transactions()
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

        with ui.card().classes("w-full p-6"):
            ui.label("Collection Effectiveness Analysis").classes(
                "text-2xl font-bold mb-4"
            )

            with ui.tabs().classes("w-full") as tabs:
                strategy_tab = ui.tab("Strategy Effectiveness")
                performance_tab = ui.tab("Collection Performance")
                patterns_tab = ui.tab("Payment Patterns")

            with ui.tab_panels(tabs, value=strategy_tab).classes("w-full mt-4"):
                with ui.tab_panel(strategy_tab):
                    self._render_strategy_effectiveness(metrics)
                with ui.tab_panel(performance_tab):
                    self._render_collection_performance(metrics)
                with ui.tab_panel(patterns_tab):
                    self._render_payment_patterns(metrics)

    def _render_strategy_effectiveness(self, metrics):
        try:
            if "strategy_success" in metrics:
                status_data = []
                for status, status_metrics in metrics["strategy_success"].items():
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

                                for status in statuses:
                                    if status in metrics["strategy_success"]:
                                        status_metrics = metrics["strategy_success"][
                                            status
                                        ]
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
            print(f"Error rendering strategy effectiveness: {str(e)}")
            with ui.card().classes("w-full p-4"):
                ui.label(
                    "No data available for strategy effectiveness analysis"
                ).classes("text-lg")

    def _render_collection_performance(self, metrics):
        try:
            transactions_df = self.get_transactions()

            if not transactions_df.empty:
                # Create a copy and ensure proper data types
                valid_payments = transactions_df[
                    transactions_df["payment_amount"] > 0
                ].copy()

                # Convert payment amount to numeric
                valid_payments["payment_amount"] = pd.to_numeric(
                    valid_payments["payment_amount"], errors="coerce"
                )

                # Handle date conversion
                valid_payments["payment_year"] = valid_payments["payment_date_year"]
                valid_payments["payment_month"] = valid_payments["payment_date_month"]
                valid_payments["payment_month_str"] = valid_payments.apply(
                    lambda x: f"{x['payment_year']}-{x['payment_month']:02d}", axis=1
                )

                if len(valid_payments) > 0:
                    # Monthly payment analysis using the string month field
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

                    # Flatten column names
                    monthly_stats.columns = [
                        "month",
                        "payment_count",
                        "total_amount",
                        "avg_payment",
                        "unique_accounts",
                    ]

                    # Sort by month to ensure chronological order
                    monthly_stats = monthly_stats.sort_values("month")

                    if len(monthly_stats) > 0:
                        # Create monthly performance chart
                        performance_chart = {
                            "chart": {"type": "column"},
                            "title": {"text": "Monthly Collection Performance"},
                            "xAxis": {
                                "categories": monthly_stats["month"].tolist(),
                                "title": {"text": "Month"},
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

                        # Add performance metrics cards
                        with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
                            # Overall Performance
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

                            # Payment Size Distribution
                            with ui.card().classes("p-4"):
                                ui.label("Payment Size Distribution").classes(
                                    "text-lg font-bold mb-2"
                                )
                                payment_ranges = [
                                    (0, 100),
                                    (100, 500),
                                    (500, 1000),
                                    (1000, 5000),
                                    (5000, float("inf")),
                                ]
                                with ui.column().classes("gap-2"):
                                    for low, high in payment_ranges:
                                        mask = valid_payments["payment_amount"] > low
                                        if high != float("inf"):
                                            mask &= (
                                                valid_payments["payment_amount"] <= high
                                            )
                                        count = len(valid_payments[mask])
                                        range_text = (
                                            f"${low:,} - ${high:,}"
                                            if high != float("inf")
                                            else f"${low:,}+"
                                        )
                                        ui.label(f"{range_text}: {count:,} payments")

                            # Recent Activity
                            with ui.card().classes("p-4"):
                                ui.label("Recent Activity").classes(
                                    "text-lg font-bold mb-2"
                                )
                                with ui.column().classes("gap-2"):
                                    if len(monthly_stats) >= 2:
                                        current = monthly_stats.iloc[-1]
                                        previous = monthly_stats.iloc[-2]

                                        if (
                                            previous["total_amount"] > 0
                                            and previous["payment_count"] > 0
                                        ):
                                            amount_change = (
                                                (
                                                    current["total_amount"]
                                                    / previous["total_amount"]
                                                )
                                                - 1
                                            ) * 100
                                            count_change = (
                                                (
                                                    current["payment_count"]
                                                    / previous["payment_count"]
                                                )
                                                - 1
                                            ) * 100

                                            ui.label(
                                                f"Amount Change: {amount_change:+.1f}%"
                                            )
                                            ui.label(
                                                f"Count Change: {count_change:+.1f}%"
                                            )

                                    latest = monthly_stats.iloc[-1]
                                    ui.label("Current Month:")
                                    ui.label(
                                        f"Collections: ${latest['total_amount']:,.2f}"
                                    )
                                    ui.label(
                                        f"Active Accounts: {latest['unique_accounts']:,}"
                                    )
                    else:
                        with ui.card().classes("w-full p-4"):
                            ui.label("No monthly statistics available").classes(
                                "text-lg"
                            )
                else:
                    with ui.card().classes("w-full p-4"):
                        ui.label("No valid payments found").classes("text-lg")
            else:
                with ui.card().classes("w-full p-4"):
                    ui.label("No transaction data available").classes("text-lg")

        except Exception as e:
            print(f"Error rendering collection performance: {str(e)}")
            import traceback

            print(traceback.format_exc())
            with ui.card().classes("w-full p-4"):
                ui.label("Error processing collection performance data").classes(
                    "text-lg"
                )

    def _render_payment_patterns(self, metrics):
        try:
            transactions_df = self.get_transactions()

            if not transactions_df.empty:
                valid_payments = transactions_df[
                    transactions_df["payment_amount"] > 0
                ].copy()
                valid_payments["payment_amount"] = pd.to_numeric(
                    valid_payments["payment_amount"], errors="coerce"
                )

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
                                day_names[int(d)] for d in daily_stats["day_of_week"]
                            ],
                            "title": {"text": "Day of Week"},
                        },
                        "yAxis": [
                            {
                                "title": {"text": "Amount ($)"},
                                "labels": {"format": "${value:,.0f}"},
                            },
                            {"title": {"text": "Number of Payments"}, "opposite": True},
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
                                percentiles = valid_payments["payment_amount"].quantile(
                                    [0.25, 0.5, 0.75]
                                )
                                ui.label(f"25th Percentile: ${percentiles[0.25]:,.2f}")
                                ui.label(f"Median Payment: ${percentiles[0.5]:,.2f}")
                                ui.label(f"75th Percentile: ${percentiles[0.75]:,.2f}")
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
                with ui.card().classes("w-full p-4"):
                    ui.label("No transaction data available").classes("text-lg")

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
