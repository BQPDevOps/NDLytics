# from nicegui import ui
# import pandas as pd


# class CallAnalyticsWidget:
#     def __init__(self, calls_df):
#         """
#         Widget to analyze call campaign performance.

#         Args:
#             calls_df (pd.DataFrame): DataFrame from OD_Master.csv
#         """
#         self.calls_df = calls_df.copy()
#         self._preprocess_data()

#     def _preprocess_data(self):
#         """Prepare call data for analysis."""
#         # Convert date components to datetime
#         self.calls_df["call_date"] = pd.to_datetime(
#             self.calls_df[
#                 [
#                     "call_completed_date_year",
#                     "call_completed_date_month",
#                     "call_completed_date_day",
#                 ]
#             ]
#             .astype(str)
#             .agg("-".join, axis=1)
#         )

#         # Create month-year field for grouping
#         self.calls_df["month_year"] = self.calls_df["call_date"].dt.strftime("%Y-%m")

#         # Calculate key metrics
#         self._calculate_metrics()

#     def _calculate_metrics(self):
#         """Calculate call campaign performance metrics."""
#         # Monthly call totals and outcomes
#         self.monthly_metrics = (
#             self.calls_df.groupby("month_year")
#             .agg(
#                 {
#                     "call_id": "count",
#                     "delivery_cost": "sum",
#                     "delivery_length": "mean",
#                     "file_number": "nunique",
#                 }
#             )
#             .reset_index()
#         )

#         # Calculate contact rate
#         contact_counts = (
#             self.calls_df.groupby("month_year")["interaction"]
#             .apply(lambda x: (x != "No Answer").sum())
#             .reset_index()
#         )
#         self.monthly_metrics["contact_rate"] = (
#             contact_counts["interaction"] / self.monthly_metrics["call_id"] * 100
#         )

#         # Calculate cost per contact
#         self.monthly_metrics["cost_per_call"] = (
#             self.monthly_metrics["delivery_cost"] / self.monthly_metrics["call_id"]
#         )

#         # Sort by month-year
#         self.monthly_metrics = self.monthly_metrics.sort_values("month_year")

#     def render(self):
#         """Render the call analytics dashboard."""
#         with ui.card().classes("w-full p-4 gap-4"):
#             ui.label("Call Campaign Analytics").classes("text-xl font-bold")

#             # Create tabs for different views
#             with ui.tabs().classes("w-full") as tabs:
#                 volume_tab = ui.tab("Call Volume")
#                 performance_tab = ui.tab("Performance")
#                 cost_tab = ui.tab("Cost Analysis")

#             with ui.tab_panels(tabs, value=volume_tab).classes("w-full"):
#                 with ui.tab_panel(volume_tab):
#                     self._render_volume_analysis()

#                 with ui.tab_panel(performance_tab):
#                     self._render_performance_metrics()

#                 with ui.tab_panel(cost_tab):
#                     self._render_cost_analysis()

#     def _render_volume_analysis(self):
#         """Render call volume trends."""
#         chart_data = {
#             "title": {"text": "Monthly Call Volume"},
#             "xAxis": {"categories": self.monthly_metrics["month_year"].tolist()},
#             "yAxis": [
#                 {"title": {"text": "Number of Calls"}},
#                 {"title": {"text": "Unique Accounts"}, "opposite": True},
#             ],
#             "series": [
#                 {
#                     "name": "Total Calls",
#                     "type": "column",
#                     "data": self.monthly_metrics["call_id"].tolist(),
#                 },
#                 {
#                     "name": "Unique Accounts",
#                     "type": "line",
#                     "data": self.monthly_metrics["file_number"].tolist(),
#                     "yAxis": 1,
#                 },
#             ],
#         }

#         ui.highchart(chart_data).classes("w-full h-64")

#     def _render_performance_metrics(self):
#         """Render contact rate and other performance metrics."""
#         chart_data = {
#             "title": {"text": "Contact Rate Trends"},
#             "xAxis": {"categories": self.monthly_metrics["month_year"].tolist()},
#             "yAxis": {"title": {"text": "Contact Rate (%)"}, "max": 100},
#             "series": [
#                 {
#                     "name": "Contact Rate",
#                     "type": "line",
#                     "data": self.monthly_metrics["contact_rate"].round(1).tolist(),
#                 }
#             ],
#         }

#         ui.highchart(chart_data).classes("w-full h-64")

#         # Add interaction breakdown
#         interaction_dist = (
#             self.calls_df["interaction"]
#             .value_counts(normalize=True)
#             .multiply(100)
#             .round(1)
#         )

#         with ui.grid(columns=3).classes("w-full gap-4 mt-4"):
#             for interaction, percentage in interaction_dist.items():
#                 with ui.card().classes("p-4"):
#                     ui.label(interaction).classes("text-lg font-bold")
#                     ui.label(f"{percentage}%")

#     def _render_cost_analysis(self):
#         """Render cost analysis metrics."""
#         with ui.grid(columns=2).classes("w-full gap-4"):
#             # Cost trend chart
#             chart_data = {
#                 "title": {"text": "Cost per Call Trend"},
#                 "xAxis": {"categories": self.monthly_metrics["month_year"].tolist()},
#                 "yAxis": {
#                     "title": {"text": "Cost ($)"},
#                     "labels": {"format": "${value:.2f}"},
#                 },
#                 "series": [
#                     {
#                         "name": "Cost per Call",
#                         "type": "line",
#                         "data": self.monthly_metrics["cost_per_call"].round(2).tolist(),
#                     }
#                 ],
#             }

#             ui.highchart(chart_data).classes("w-full h-64")

#             # Summary metrics
#             with ui.card().classes("p-4"):
#                 ui.label("Cost Summary").classes("text-lg font-bold mb-4")

#                 total_cost = self.calls_df["delivery_cost"].sum()
#                 total_calls = len(self.calls_df)
#                 avg_cost = total_cost / total_calls

#                 ui.label(f"Total Cost: ${total_cost:,.2f}")
#                 ui.label(f"Average Cost per Call: ${avg_cost:.2f}")
#                 ui.label(f"Total Calls: {total_calls:,}")


# def create_call_analytics_widget(calls_df):
#     """Factory function to create a new CallAnalyticsWidget instance."""
#     return CallAnalyticsWidget(calls_df)
