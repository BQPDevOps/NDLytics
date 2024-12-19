from nicegui import ui
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Any
from middleware.groq import GroqMiddleware
from .WidgetFramework import WidgetFramework


class CollectionInsightsWidget(WidgetFramework):
    """
    A widget that combines data analysis with AI-generated insights to provide
    comprehensive understanding of collection patterns and trends.
    """

    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)
        self.groq = GroqMiddleware(
            model="llama3-70b-8192",
            temperature=0.0,
            max_tokens=1000,
        )
        self.insights_cache = {}

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _calculate_metrics(self):
        """Calculate all metrics and cache them"""
        # Calculate key metrics
        self._preprocess_data()

        # Structure metrics properly
        metrics = {
            "payment_patterns": {
                "total_collected": float(self.payment_patterns["total_collected"]),
                "avg_payment": float(self.payment_patterns["avg_payment"]),
                "payment_count": int(self.payment_patterns["payment_count"]),
                "unique_accounts": int(self.payment_patterns["unique_accounts"]),
            },
            "status_patterns": {
                str(k): int(v) for k, v in self.status_patterns.items()
            },
            "time_metrics": {
                "avg_days_to_payment": float(self.time_metrics["avg_days_to_payment"]),
                "recent_trend": {
                    "recent_total": float(
                        self.time_metrics["recent_trend"]["recent_total"]
                    ),
                    "previous_total": float(
                        self.time_metrics["recent_trend"]["previous_total"]
                    ),
                    "change_percentage": float(
                        self.time_metrics["recent_trend"]["change_percentage"]
                    ),
                },
            },
            "insights": {},  # Add insights cache to metrics
            "last_modified": int(datetime.now().timestamp()),
        }

        # Generate and cache all insights upfront
        for analysis_type in ["payment_patterns", "status_trends", "recommendations"]:
            prompt_template, variables = self._generate_analysis_prompt(analysis_type)
            variables["question"] = "Provide analysis based on the above data."
            metrics["insights"][analysis_type] = self.groq.generate_response(
                prompt=prompt_template, variables=variables
            )

        # Update cache
        self.update_metric_cache(metrics)

    def _preprocess_data(self):
        """Prepare data for analysis and insight generation."""
        transactions_df = self.get_transactions()
        comments_df = self.get_contacts()
        accounts_df = self.get_accounts()

        # Create datetime fields
        def create_date(df, year_col, month_col, day_col):
            # Create a copy to avoid modifying original
            date_df = df[[year_col, month_col, day_col]].copy()

            # Fill NA/inf values with defaults
            date_df[year_col] = pd.to_numeric(
                date_df[year_col], errors="coerce"
            ).fillna(1900)
            date_df[month_col] = pd.to_numeric(
                date_df[month_col], errors="coerce"
            ).fillna(1)
            date_df[day_col] = pd.to_numeric(date_df[day_col], errors="coerce").fillna(
                1
            )

            # Convert to integers after handling NA/inf
            date_df[year_col] = date_df[year_col].astype(int)
            date_df[month_col] = date_df[month_col].astype(int).clip(1, 12)
            date_df[day_col] = date_df[day_col].astype(int).clip(1, 31)

            # Format with zero-padding
            date_strings = (
                date_df[year_col].astype(str)
                + "-"
                + date_df[month_col].map(lambda x: f"{x:02d}")
                + "-"
                + date_df[day_col].map(lambda x: f"{x:02d}")
            )

            # Convert to datetime
            return pd.to_datetime(date_strings, format="%Y-%m-%d", errors="coerce")

        transactions_df["date"] = create_date(
            transactions_df,
            "posted_date_year",
            "posted_date_month",
            "posted_date_day",
        )

        comments_df["date"] = create_date(
            comments_df,
            "created_date_year",
            "created_date_month",
            "created_date_day",
        )

        # Calculate metrics for insight generation
        self.payment_patterns = {
            "total_collected": transactions_df["payment_amount"].sum(),
            "avg_payment": transactions_df["payment_amount"].mean(),
            "payment_count": len(transactions_df),
            "unique_accounts": transactions_df["file_number"].nunique(),
        }

        # Status patterns
        self.status_patterns = comments_df["account_status"].value_counts()

        # Time-based metrics
        self.time_metrics = self._calculate_time_metrics(transactions_df)

    def _calculate_time_metrics(self, transactions_df):
        """Calculate time metrics safely without recursion"""
        try:
            # Calculate average days between min and max dates for each account
            account_dates = transactions_df.groupby("file_number")["date"].agg(
                ["min", "max"]
            )
            account_dates["days_diff"] = (
                account_dates["max"] - account_dates["min"]
            ).dt.days
            avg_days = account_dates["days_diff"].mean()

            if pd.isna(avg_days):
                avg_days = 0.0

            recent_trend = self._calculate_recent_trend(transactions_df)

            return {
                "avg_days_to_payment": float(avg_days),
                "recent_trend": recent_trend,
            }
        except Exception as e:
            print(f"Error calculating time metrics: {str(e)}")
            return {
                "avg_days_to_payment": 0.0,
                "recent_trend": {
                    "recent_total": 0.0,
                    "previous_total": 0.0,
                    "change_percentage": 0.0,
                },
            }

    def _calculate_recent_trend(self, transactions_df):
        """Calculate recent collection trends safely."""
        try:
            recent_cutoff = datetime.now() - timedelta(days=30)

            # Calculate recent payments
            recent_mask = transactions_df["date"] >= recent_cutoff
            recent_payments = transactions_df[recent_mask]["payment_amount"].sum()

            # Calculate previous payments
            prev_cutoff = recent_cutoff - timedelta(days=30)
            prev_mask = (transactions_df["date"] < recent_cutoff) & (
                transactions_df["date"] >= prev_cutoff
            )
            previous_payments = transactions_df[prev_mask]["payment_amount"].sum()

            # Calculate change percentage
            if previous_payments > 0:
                change_percentage = (
                    (recent_payments - previous_payments) / previous_payments
                ) * 100
            else:
                change_percentage = 0.0

            return {
                "recent_total": float(recent_payments),
                "previous_total": float(previous_payments),
                "change_percentage": float(change_percentage),
            }
        except Exception as e:
            print(f"Error calculating recent trend: {str(e)}")
            return {
                "recent_total": 0.0,
                "previous_total": 0.0,
                "change_percentage": 0.0,
            }

    def _generate_analysis_prompt(self, analysis_type: str) -> tuple[str, dict]:
        """Generate a prompt template and variables for the Groq API."""
        cached_metrics = super().get_cached()  # Use parent's get_cached directly

        if not cached_metrics:
            return "", {}  # Return empty if no metrics available

        if analysis_type == "payment_patterns":
            try:
                metrics_for_prompt = {
                    "Payment Metrics": {
                        "Total Collections": f"${cached_metrics['payment_patterns']['total_collected']:,.2f}",
                        "Average Payment": f"${cached_metrics['payment_patterns']['avg_payment']:,.2f}",
                        "Total Payments": f"{cached_metrics['payment_patterns']['payment_count']:,}",
                        "Unique Accounts": f"{cached_metrics['payment_patterns']['unique_accounts']:,}",
                    },
                    "Recent Trends": {
                        "Last 30 Days": f"${cached_metrics['time_metrics']['recent_trend']['recent_total']:,.2f}",
                        "Previous 30 Days": f"${cached_metrics['time_metrics']['recent_trend']['previous_total']:,.2f}",
                        "Change": f"{cached_metrics['time_metrics']['recent_trend']['change_percentage']:,.1f}%",
                    },
                }

                prompt_template = """
                You are an expert collections analyst. Analyze the following payment metrics
                and provide 3-4 clear, actionable insights about payment patterns and trends.
                Focus on what the data suggests about collection effectiveness and areas for
                improvement. Keep each insight to 2-3 sentences.

                Metrics:
                {metrics_json}

                Provide your analysis in clear, professional language that a business user
                would understand. Focus on practical implications and actionable insights.
                """

                return prompt_template, {
                    "metrics_json": json.dumps(metrics_for_prompt, indent=2)
                }
            except Exception as e:
                print(f"Error generating payment patterns prompt: {str(e)}")
                return "", {}

        elif analysis_type == "status_trends":
            try:
                status_counts = cached_metrics.get("status_patterns", {})
                prompt_template = """
                You are an expert collections analyst. Analyze the following account status
                distribution and provide 3-4 clear, actionable insights about account
                management patterns. Focus on what the status distribution suggests about
                collection strategy effectiveness. Keep each insight to 2-3 sentences.

                Status Distribution:
                {status_json}

                Provide your analysis in clear, professional language that a business user
                would understand. Focus on practical implications and suggested actions.
                """

                return prompt_template, {
                    "status_json": json.dumps(status_counts, indent=2)
                }
            except Exception as e:
                print(f"Error generating status trends prompt: {str(e)}")
                return "", {}

        elif analysis_type == "recommendations":
            try:
                metrics_for_prompt = {
                    "Performance Metrics": {
                        "Average Days to Payment": f"{cached_metrics['time_metrics']['avg_days_to_payment']:.1f}",
                        "Collection Rate": f"{(cached_metrics['payment_patterns']['unique_accounts'] / len(self.get_accounts()) * 100):.1f}%",
                        "Recent Trend": f"{cached_metrics['time_metrics']['recent_trend']['change_percentage']:,.1f}%",
                    }
                }

                prompt_template = """
                You are an expert collections analyst. Based on the following performance
                metrics, provide 3-4 specific, actionable recommendations for improving
                collection effectiveness. Each recommendation should be practical and
                specific. Keep each recommendation to 2-3 sentences.

                Metrics:
                {metrics_json}

                Provide your recommendations in clear, professional language that a business
                user would understand. Focus on concrete, implementable actions.
                """

                return prompt_template, {
                    "metrics_json": json.dumps(metrics_for_prompt, indent=2)
                }
            except Exception as e:
                print(f"Error generating recommendations prompt: {str(e)}")
                return "", {}

        return "", {}

    def _get_insights(self, analysis_type: str) -> str:
        """
        Get AI-generated insights for the specified analysis type.
        Uses caching to avoid repeated API calls.
        """
        metrics = self.get_cached()
        return metrics.get("insights", {}).get(analysis_type, "No insights available")

    def render(self):
        """Render the complete insights dashboard."""
        metrics = self.get_cached()

        with ui.card().classes("w-full p-6"):
            ui.label("Collection Intelligence Analysis").classes(
                "text-2xl font-bold mb-4"
            )

            # Create insight category tabs
            with ui.tabs().classes("w-full") as tabs:
                patterns_tab = ui.tab("Payment Patterns")
                status_tab = ui.tab("Status Analysis")
                recommendations_tab = ui.tab("Recommendations")

            with ui.tab_panels(tabs, value=patterns_tab).classes("w-full mt-4"):
                with ui.tab_panel(patterns_tab):
                    self._render_payment_insights(metrics)

                with ui.tab_panel(status_tab):
                    self._render_status_insights(metrics)

                with ui.tab_panel(recommendations_tab):
                    self._render_recommendations(metrics)

    def _render_payment_insights(self, metrics):
        """Render payment pattern analysis and insights."""
        if not metrics or not isinstance(metrics, dict):
            metrics = self.get_cached()

        with ui.grid(columns=2).classes("w-full gap-6"):
            # Metrics card
            with ui.card().classes("p-4"):
                ui.label("Payment Metrics").classes("text-lg font-bold mb-4")

                with ui.column().classes("gap-3"):
                    metric_items = [
                        (
                            "Total Collections",
                            f"${metrics.get('payment_patterns', {}).get('total_collected', 0):,.2f}",
                        ),
                        (
                            "Average Payment",
                            f"${metrics.get('payment_patterns', {}).get('avg_payment', 0):,.2f}",
                        ),
                        (
                            "Total Payments",
                            f"{metrics.get('payment_patterns', {}).get('payment_count', 0):,}",
                        ),
                        (
                            "Unique Accounts",
                            f"{metrics.get('payment_patterns', {}).get('unique_accounts', 0):,}",
                        ),
                    ]

                    for label, value in metric_items:
                        with ui.row().classes("w-full justify-between"):
                            ui.label(label).classes("text-gray-600")
                            ui.label(value).classes("font-bold")

            # Trend card
            with ui.card().classes("p-4"):
                ui.label("Recent Trends").classes("text-lg font-bold mb-4")

                with ui.column().classes("gap-3"):
                    recent_trend = metrics.get("time_metrics", {}).get(
                        "recent_trend", {}
                    )
                    trends = [
                        (
                            "Last 30 Days",
                            f"${recent_trend.get('recent_total', 0):,.2f}",
                        ),
                        (
                            "Previous 30 Days",
                            f"${recent_trend.get('previous_total', 0):,.2f}",
                        ),
                        (
                            "Change",
                            f"{recent_trend.get('change_percentage', 0):,.1f}%",
                        ),
                    ]

                    for label, value in trends:
                        with ui.row().classes("w-full justify-between"):
                            ui.label(label).classes("text-gray-600")
                            ui.label(value).classes("font-bold")

        # AI Insights
        with ui.card().classes("p-4 mt-6"):
            ui.label("AI-Generated Insights").classes("text-lg font-bold mb-4")
            insights = self._get_insights("payment_patterns")
            with ui.column().classes("gap-4"):
                self._render_formatted_text(insights)

    def _render_status_insights(self, metrics):
        """Render status distribution analysis and insights."""
        # Create status distribution chart
        chart_data = {
            "chart": {"type": "pie"},
            "title": {"text": "Account Status Distribution"},
            "series": [
                {
                    "name": "Accounts",
                    "data": [
                        {"name": status, "y": count}
                        for status, count in metrics["status_patterns"].items()
                    ],
                }
            ],
        }

        ui.highchart(chart_data).classes("w-full h-64")

        # AI Insights
        with ui.card().classes("p-4 mt-6"):
            ui.label("AI-Generated Insights").classes("text-lg font-bold mb-4")
            insights = self._get_insights("status_trends")
            with ui.column().classes("gap-4"):
                self._render_formatted_text(insights)

    def _render_recommendations(self, metrics):
        """Render AI-generated recommendations for improvement."""
        with ui.card().classes("p-4"):
            ui.label("Strategic Recommendations").classes("text-lg font-bold mb-4")
            recommendations = self._get_insights("recommendations")
            with ui.column().classes("gap-4"):
                self._render_formatted_text(recommendations, with_card=True)

    def _render_formatted_text(self, text: str, with_card: bool = False):
        """Helper method to render formatted text with proper styling"""
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Handle bold text (enclosed in **)
            if "**" in line:
                # Split into parts by **
                parts = line.split("**")
                for i, part in enumerate(parts):
                    if not part:
                        continue

                    # Odd indices were inside ** in original text
                    if i % 2 == 1:
                        ui.label(part).classes("font-semibold text-gray-900")
                    else:
                        if part.strip():
                            if with_card:
                                with ui.card().classes("p-4 bg-blue-50"):
                                    ui.label(part.strip()).classes("text-gray-700")
                            else:
                                ui.label(part.strip()).classes("text-gray-700")
            else:
                if with_card:
                    with ui.card().classes("p-4 bg-blue-50"):
                        ui.label(line).classes("text-gray-700")
                else:
                    ui.label(line).classes("text-gray-700")

    def get_cached(self):
        """Override get_cached to ensure proper data structure"""
        if self.force_refresh:
            self._calculate_metrics()
            return super().get_cached()

        cached = super().get_cached()

        # Return cached data if valid
        if isinstance(cached, dict) and all(
            key in cached
            for key in [
                "payment_patterns",
                "status_patterns",
                "time_metrics",
                "insights",
            ]
        ):
            return cached

        # If we get here, we need to recalculate
        self._calculate_metrics()
        return super().get_cached()


def create_collection_insights_widget(
    widget_configuration: dict = None, force_refresh=False
):
    """Factory function to create a new CollectionInsightsWidget instance."""
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["accounts", "transactions", "contacts"],
            "company_id": "ALL",
            "widget_id": "wgt_collection_insights",
            "force_refresh": force_refresh,
        }
    return CollectionInsightsWidget(widget_configuration)
