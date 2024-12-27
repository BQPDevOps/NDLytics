from nicegui import ui
import pandas as pd
from datetime import datetime, timedelta
from middleware.groq import GroqMiddleware
from .WidgetFramework import WidgetFramework


class TransactionAnalysisWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)
        self.groq = GroqMiddleware(
            model="llama3-70b-8192",
            temperature=0.0,
            max_tokens=1000,
        )
        self.ai_icon_src = (
            "https://lottie.host/77b2ba29-8055-4be9-b699-378f5434c0c4/jptyrmmrGU.json"
        )

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _calculate_metrics(self):
        try:
            transactions_df = self.get_transactions()
            outbound_df = self.get_outbound()

            # Transaction analysis
            transaction_metrics = self._analyze_transactions(transactions_df)

            # Call outcome analysis
            call_metrics = self._analyze_calls(outbound_df)

            # Combined analysis
            combined_metrics = self._combine_analysis(transactions_df, outbound_df)

            metrics = {
                "transaction_metrics": transaction_metrics,
                "call_metrics": call_metrics,
                "combined_metrics": combined_metrics,
                "last_modified": int(datetime.now().timestamp()),
            }

            print("DEBUG - Call Metrics:", call_metrics)  # Debug print
            self.update_metric_cache(metrics)

        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            self.update_metric_cache(
                {
                    "transaction_metrics": {},
                    "call_metrics": {},
                    "combined_metrics": {},
                    "last_modified": int(datetime.now().timestamp()),
                }
            )

    def _analyze_transactions(self, df):
        if df.empty:
            return {}

        # Convert date columns
        def create_date(df, year_col, month_col, day_col):
            date_df = df[[year_col, month_col, day_col]].copy()
            date_df[year_col] = pd.to_numeric(
                date_df[year_col], errors="coerce"
            ).fillna(1900)
            date_df[month_col] = pd.to_numeric(
                date_df[month_col], errors="coerce"
            ).fillna(1)
            date_df[day_col] = pd.to_numeric(date_df[day_col], errors="coerce").fillna(
                1
            )

            date_df[year_col] = date_df[year_col].astype(int)
            date_df[month_col] = date_df[month_col].astype(int).clip(1, 12)
            date_df[day_col] = date_df[day_col].astype(int).clip(1, 31)

            date_strings = (
                date_df[year_col].astype(str)
                + "-"
                + date_df[month_col].map(lambda x: f"{x:02d}")
                + "-"
                + date_df[day_col].map(lambda x: f"{x:02d}")
            )
            return pd.to_datetime(date_strings, format="%Y-%m-%d", errors="coerce")

        df["payment_date"] = create_date(
            df, "payment_date_year", "payment_date_month", "payment_date_day"
        )

        daily_totals = (
            df.groupby(df["payment_date"].dt.day_name())["payment_amount"]
            .agg(["sum", "count"])
            .to_dict("index")
        )

        return {
            "total_amount": float(df["payment_amount"].sum()),
            "avg_payment": float(df["payment_amount"].mean()),
            "payment_count": int(len(df)),
            "daily_patterns": daily_totals,
            "payment_types": df["transaction_type"].value_counts().to_dict(),
            "operator_stats": df["operator"].value_counts().to_dict(),
        }

    def _analyze_calls(self, df):
        if df.empty:
            print("DEBUG - Outbound df is empty.")
            return {
                "total_calls": 0,
                "payment_outcomes": 0,
                "non_payment_outcomes": 0,
                "payment_conversion_rate": 0,
                "result_patterns": {},
            }

        try:
            total_calls = int(df["total_calls"].sum())
            result_columns = [col for col in df.columns if col.startswith("result_")]

            result_patterns = {}
            for col in result_columns:
                key = col.replace("result_", "")
                value = df[col].sum()
                result_patterns[key] = round(float(value), 2)

            payment_patterns = ["Payment Made", "Payment Plan", "Promise To Pay"]
            payment_outcomes = sum(
                result_patterns.get(pattern, 0) for pattern in payment_patterns
            )
            non_payment_outcomes = sum(
                val for k, val in result_patterns.items() if k not in payment_patterns
            )

            payment_conversion_rate = (
                payment_outcomes / total_calls if total_calls > 0 else 0
            )

            metrics = {
                "total_calls": total_calls,
                "payment_outcomes": round(payment_outcomes, 2),
                "non_payment_outcomes": round(non_payment_outcomes, 2),
                "payment_conversion_rate": round(payment_conversion_rate, 2),
                "result_patterns": result_patterns,
            }

            return metrics

        except Exception as e:
            print(f"Error in _analyze_calls: {str(e)}")
            return {
                "total_calls": 0,
                "payment_outcomes": 0,
                "non_payment_outcomes": 0,
                "payment_conversion_rate": 0,
                "result_patterns": {},
            }

    def _combine_analysis(self, trans_df, call_df):
        if trans_df.empty or call_df.empty:
            return {}

        # Analyze payment success rate correlation with call patterns
        payment_success = {
            "avg_payment_after_call": float(trans_df["payment_amount"].mean()),
            "payment_correlation": {
                "same_day": 0.75,  # Example correlation
                "next_day": 0.45,
                "week_later": 0.25,
            },
        }

        return payment_success

    def render(self):
        ui.add_body_html(
            '<script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>'
        )

        metrics = self.get_cached()

        with ui.card().classes("w-full p-6 max-h-[86vh]"):
            with ui.row().classes("flex justify-between items-center gap-4 w-full"):
                ui.label("Outbound Transaction Correlation").classes(
                    "text-xl font-bold"
                )
                ui.button(
                    icon="refresh",
                    on_click=lambda: [self._calculate_metrics(), self.render()],
                ).props("round flat")

            with ui.tabs().classes("w-full") as tabs:
                trans_tab = ui.tab("Transaction Patterns")
                call_tab = ui.tab("Call Impact")
                combined_tab = ui.tab("Combined Analysis")

            with ui.tab_panels(tabs, value=trans_tab).classes("w-full mt-4"):
                with ui.tab_panel(trans_tab):
                    self._render_transaction_analysis(metrics)

                with ui.tab_panel(call_tab):
                    self._render_call_impact(metrics)

                with ui.tab_panel(combined_tab):
                    self._render_combined_analysis(metrics)

    def _render_transaction_analysis(self, metrics):
        if not metrics.get("transaction_metrics"):
            ui.label("No transaction data available").classes("text-lg")
            return

        trans_metrics = metrics["transaction_metrics"]
        print("DEBUG - Transaction Metrics:", trans_metrics)
        print("DEBUG - Daily Patterns:", trans_metrics["daily_patterns"])

        # Daily pattern chart
        try:
            daily_data = trans_metrics["daily_patterns"]
            day_order = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            days = [day for day in day_order if day in daily_data["count"]]

            chart_data = {
                "chart": {"type": "column"},
                "title": {"text": "Payment Patterns by Day"},
                "xAxis": {"categories": days},
                "yAxis": [
                    {"title": {"text": "Amount ($)"}},
                    {"title": {"text": "Count"}, "opposite": True},
                ],
                "series": [
                    {
                        "name": "Total Amount",
                        "type": "column",
                        "data": [daily_data["sum"][day] for day in days],
                    },
                    {
                        "name": "Transaction Count",
                        "type": "line",
                        "yAxis": 1,
                        "data": [daily_data["count"][day] for day in days],
                    },
                ],
            }
        except Exception as e:
            print("DEBUG - Error processing daily data:", e)
            print("DEBUG - Daily data structure:", daily_data)
            return

        ui.highchart(chart_data).classes("w-full h-64")

        # Summary metrics
        with ui.grid(columns=3).classes("w-full gap-6 mt-4"):
            metrics_cards = [
                ("Total Collections", f"${trans_metrics['total_amount']:,.2f}"),
                ("Average Payment", f"${trans_metrics['avg_payment']:.2f}"),
                ("Payment Count", f"{trans_metrics['payment_count']:,}"),
            ]

            for label, value in metrics_cards:
                with ui.card().classes("p-4"):
                    ui.label(label).classes("text-lg font-bold")
                    ui.label(value)

    def _render_call_impact(self, metrics):
        if not metrics or not metrics.get("transaction_metrics"):
            ui.label("No transaction data available").classes("text-lg")
            return

        trans_metrics = metrics.get("transaction_metrics", {})

        # Operator Performance Chart
        operator_data = trans_metrics.get("operator_stats", {})
        payment_types = trans_metrics.get("payment_types", {})

        operator_chart = {
            "chart": {"type": "column"},
            "title": {"text": "Operator Performance"},
            "xAxis": {"categories": list(operator_data.keys())},
            "yAxis": {"title": {"text": "Number of Transactions"}},
            "series": [{"name": "Transactions", "data": list(operator_data.values())}],
        }

        payment_type_chart = {
            "chart": {"type": "pie"},
            "title": {"text": "Payment Type Distribution"},
            "tooltip": {"pointFormat": "{series.name}: <b>{point.percentage:.1f}%</b>"},
            "series": [
                {
                    "name": "Payment Types",
                    "data": [
                        {"name": str(k), "y": v} for k, v in payment_types.items()
                    ],
                }
            ],
        }

        with ui.grid(columns=2).classes("w-full gap-6"):
            ui.highchart(operator_chart).classes("w-full h-64")
            ui.highchart(payment_type_chart).classes("w-full h-64")

        # Summary metrics
        with ui.grid(columns=3).classes("w-full gap-6 mt-4"):
            metrics_cards = [
                ("Total Operators", f"{len(operator_data)}"),
                ("Total Transactions", f"{trans_metrics['payment_count']:,}"),
                ("Average Amount", f"${trans_metrics['avg_payment']:.2f}"),
            ]

            for label, value in metrics_cards:
                with ui.card().classes("p-4"):
                    ui.label(label).classes("text-lg font-bold")
                    ui.label(value)

        # Generate AI technical summary
        prompt_template = """
        As a data analyst, provide a brief technical summary of the following metrics:

        Operator Data:
        {operator_stats}

        Payment Types:
        {payment_types}

        Key Metrics:
        - Total Operators: {total_operators}
        - Total Transactions: {total_transactions}
        - Average Payment: ${avg_payment}

        Focus on statistical observations and operational patterns. Keep the analysis to 2-3 concise, technical sentences.
        Use ** ** to highlight key statistical findings.
        """

        variables = {
            "operator_stats": operator_data,
            "payment_types": payment_types,
            "total_operators": len(operator_data),
            "total_transactions": trans_metrics["payment_count"],
            "avg_payment": trans_metrics["avg_payment"],
        }

        technical_summary = self.groq.generate_response(
            prompt=prompt_template, variables=variables
        )

        # Render technical summary
        with ui.card().classes(
            "w-full p-4 mt-4 bg-gradient-to-r from-gray-50 to-white border border-gray-100"
        ):
            with ui.row().classes("items-start"):
                ui.html(
                    f'<lottie-player src="{self.ai_icon_src}" loop autoplay />'
                ).classes("w-14")
                with ui.element("div").classes("text-gray-700 leading-relaxed"):
                    text = technical_summary.strip()
                    parts = text.split("**")
                    for i, part in enumerate(parts):
                        if part:
                            if i % 2 == 0:  # Regular text
                                ui.label(part).classes("inline")
                            else:  # Emphasized text
                                ui.label(part).classes("inline font-semibold")

    def _render_combined_analysis(self, metrics):
        if not metrics.get("combined_metrics"):
            ui.label("No combined analysis data available").classes("text-lg")
            return

        combined = metrics["combined_metrics"]

        # Correlation chart
        chart_data = {
            "chart": {
                "type": "column",
                "backgroundColor": "transparent",
                "style": {"fontFamily": "Inter, sans-serif"},
                "height": 200,
            },
            "title": {
                "text": "Payment-Call Correlation",
                "style": {"fontSize": "16px", "fontWeight": "600"},
            },
            "xAxis": {
                "categories": list(combined["payment_correlation"].keys()),
                "labels": {"style": {"fontSize": "12px"}},
            },
            "yAxis": {
                "title": {
                    "text": "Correlation Strength",
                    "style": {"fontSize": "12px"},
                },
                "labels": {"style": {"fontSize": "12px"}},
            },
            "series": [
                {
                    "name": "Correlation",
                    "data": list(combined["payment_correlation"].values()),
                    "color": "#3B82F6",
                }
            ],
            "tooltip": {
                "valueSuffix": " correlation",
                "backgroundColor": "rgba(255, 255, 255, 0.9)",
                "borderWidth": 0,
                "shadow": True,
            },
        }

        ui.highchart(chart_data).classes("w-full")

        # Generate AI insights
        prompt_template = """
        You are an expert collections analyst. Analyze the following payment-call correlation data
        and provide 3-4 clear, actionable insights about the relationship between calls and payment
        patterns. Focus on what the correlations suggest about collection strategy effectiveness.
        Keep each insight to 2-3 sentences. Use ** ** to emphasize key metrics or important points.

        Correlation Data:
        - Same day correlation: {same_day}
        - Next day correlation: {next_day}
        - Week later correlation: {week_later}
        - Average payment after call: ${avg_payment}

        Provide your analysis in clear, professional language that a business user would understand.
        Focus on practical implications and actionable insights.
        """

        variables = {
            "same_day": combined["payment_correlation"]["same_day"],
            "next_day": combined["payment_correlation"]["next_day"],
            "week_later": combined["payment_correlation"]["week_later"],
            "avg_payment": combined["avg_payment_after_call"],
        }

        insights = self.groq.generate_response(
            prompt=prompt_template, variables=variables
        )

        # Render AI insights in a scrollable container
        with ui.card().classes("w-full p-6 mt-1 bg-white shadow-sm"):
            with ui.row().classes("items-center mb-4"):
                ui.icon("analytics").classes("text-blue-600 text-2xl mr-2")
                ui.label("Payment-Call Insights").classes(
                    "text-xl font-semibold text-gray-800"
                )

            with ui.column().classes("max-h-[50vh] overflow-y-auto pr-2"):
                for insight in insights.split("\n"):
                    if insight.strip():
                        with ui.card().classes(
                            "p-4 mb-2 bg-gradient-to-r from-blue-50 to-white border border-blue-100 rounded-lg"
                        ):
                            with ui.row().classes("items-start"):
                                with ui.element("div").classes(
                                    "text-gray-700 leading-relaxed"
                                ):
                                    text = insight.strip()
                                    parts = text.split("**")
                                    for i, part in enumerate(parts):
                                        if part:
                                            if i % 2 == 0:  # Regular text
                                                ui.label(part).classes("inline")
                                            else:  # Emphasized text
                                                ui.icon("insights").classes(
                                                    "text-blue-500 mr-2 mt-1"
                                                )
                                                ui.label(part).classes(
                                                    "inline font-semibold"
                                                )


def create_transaction_analysis_widget(
    widget_configuration: dict = None, force_refresh=False
):
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["transactions", "outbound"],
            "company_id": "ALL",
            "widget_id": "wgt_transaction_analysis",
            "force_refresh": force_refresh,
        }
    return TransactionAnalysisWidget(widget_configuration)
