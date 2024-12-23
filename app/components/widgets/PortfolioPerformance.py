# from nicegui import ui
# import pandas as pd
# from datetime import datetime
# import numpy as np
# from .WidgetFramework import WidgetFramework
# from modules.list_manager.ListManager import ListManager


# class PortfolioPerformanceWidget(WidgetFramework):
#     def __init__(self, widget_configuration: dict):
#         super().__init__(widget_configuration)
#         self.force_refresh = widget_configuration.get("force_refresh", False)

#         # Initialize list manager and get client mappings
#         self.list_manager = ListManager()
#         self.client_map = {
#             str(item): name
#             for item, name in self.list_manager.get_list("client_map").items()
#         }

#         # Initialize tracking periods
#         self.tracking_months = 12
#         self.current_date = datetime.now()

#         if self.is_recalc_needed() or self.force_refresh:
#             self._calculate_metrics()

#     def get_cached(self):
#         """Override get_cached to handle force refresh"""
#         try:
#             if self.force_refresh:
#                 self._calculate_metrics()
#                 return super().get_cached()

#             return super().get_cached()
#         except Exception as e:
#             print(f"Error in get_cached: {str(e)}")
#             return {}

#     def _get_client_name(self, client_number):
#         """Helper to get client name from number with fallback"""
#         return self.client_map.get(client_number, f"Client {client_number}")

#     def _calculate_metrics(self):
#         """Calculate all portfolio metrics and cache them"""
#         metrics = {}

#         # Preprocess the data
#         self._preprocess_data()

#         # Calculate placement metrics
#         placement_metrics = self._calculate_placement_metrics()
#         metrics["placement_metrics"] = placement_metrics.to_dict("records")

#         # Calculate client metrics
#         client_metrics = self._calculate_client_metrics()
#         metrics["client_metrics"] = client_metrics.to_dict("records")

#         # Add timestamp
#         metrics["last_modified"] = int(datetime.now().timestamp())

#         # Update cache
#         self.update_metric_cache(metrics)

#     def _preprocess_data(self):
#         """Prepare data for analysis"""
#         accounts_df = self.get_accounts()
#         transactions_df = self.get_transactions()

#         # Create placement date
#         accounts_df["listed_date"] = pd.to_datetime(
#             accounts_df[["listed_date_year", "listed_date_month", "listed_date_day"]]
#             .astype(str)
#             .agg("-".join, axis=1),
#             errors="coerce",
#         )

#         # Create payment dates
#         transactions_df["payment_date"] = pd.to_datetime(
#             transactions_df[
#                 ["posted_date_year", "posted_date_month", "posted_date_day"]
#             ]
#             .astype(str)
#             .agg("-".join, axis=1),
#             errors="coerce",
#         )

#         # Group accounts by placement
#         accounts_df["placement_month"] = accounts_df["listed_date"].dt.strftime("%Y-%m")
#         accounts_df["placement_id"] = (
#             accounts_df["client_number"].astype(str)
#             + "_"
#             + accounts_df["placement_month"].astype(str)
#         )

#         self.processed_accounts = accounts_df
#         self.processed_transactions = transactions_df

#     def _calculate_placement_metrics(self):
#         """Calculate performance metrics for each placement"""
#         placements = []

#         for placement_id in self.processed_accounts["placement_id"].unique():
#             # Get placement details
#             placement_accounts = self.processed_accounts[
#                 self.processed_accounts["placement_id"] == placement_id
#             ]

#             placement_date = pd.to_datetime(
#                 placement_accounts["placement_month"].iloc[0]
#             )
#             client_number = placement_accounts["client_number"].iloc[0]

#             # Calculate initial metrics using original_upb_loaded instead of loaded
#             total_loaded = placement_accounts["original_upb_loaded"].sum()
#             account_count = len(placement_accounts)

#             # Calculate monthly collections for first 12 months
#             monthly_collections = []
#             for month in range(12):
#                 month_start = placement_date + pd.DateOffset(months=month)
#                 month_end = month_start + pd.DateOffset(months=1)

#                 # Get payments for placement accounts in this month
#                 month_collected = self.processed_transactions[
#                     (
#                         self.processed_transactions["file_number"].isin(
#                             placement_accounts["file_number"]
#                         )
#                     )
#                     & (self.processed_transactions["payment_date"] >= month_start)
#                     & (self.processed_transactions["payment_date"] < month_end)
#                 ]["payment_amount"].sum()

#                 monthly_collections.append(month_collected)

#             # Calculate performance metrics
#             total_collected = sum(monthly_collections)
#             liquidation_rate = (
#                 (total_collected / total_loaded * 100) if total_loaded > 0 else 0
#             )

#             # Calculate payment velocity
#             cumulative_collections = np.cumsum(monthly_collections)
#             collection_velocity = [
#                 (cum / total_collected * 100) if total_collected > 0 else 0
#                 for cum in cumulative_collections
#             ]

#             # Calculate account activation rate
#             paying_accounts = self.processed_transactions[
#                 self.processed_transactions["file_number"].isin(
#                     placement_accounts["file_number"]
#                 )
#             ]["file_number"].nunique()
#             activation_rate = (
#                 (paying_accounts / account_count * 100) if account_count > 0 else 0
#             )

#             placements.append(
#                 {
#                     "placement_id": placement_id,
#                     "client_number": client_number,
#                     "placement_date": placement_date,
#                     "total_loaded": round(total_loaded, 2),
#                     "account_count": account_count,
#                     "total_collected": round(total_collected, 2),
#                     "liquidation_rate": round(liquidation_rate, 2),
#                     "activation_rate": round(activation_rate, 2),
#                     "monthly_collections": [round(x, 2) for x in monthly_collections],
#                     "collection_velocity": [round(x, 2) for x in collection_velocity],
#                 }
#             )

#         return pd.DataFrame(placements)

#     def _calculate_client_metrics(self):
#         """Calculate aggregate performance metrics at client level"""
#         clients = []

#         for client_number in self.processed_accounts["client_number"].unique():
#             client_placements = self.processed_accounts[
#                 self.processed_accounts["client_number"] == client_number
#             ]

#             # Update to use original_upb_loaded instead of loaded
#             total_placements = len(client_placements["placement_id"].unique())
#             total_loaded = client_placements["original_upb_loaded"].sum()
#             total_collected = self.processed_transactions[
#                 self.processed_transactions["file_number"].isin(
#                     client_placements["file_number"]
#                 )
#             ]["payment_amount"].sum()
#             total_accounts = len(client_placements)

#             client_payments = self.processed_transactions[
#                 self.processed_transactions["file_number"].isin(
#                     client_placements["file_number"]
#                 )
#             ]
#             paying_accounts = client_payments["file_number"].nunique()
#             avg_liquidation = (
#                 (total_collected / total_loaded * 100) if total_loaded > 0 else 0
#             )
#             avg_activation = (
#                 (paying_accounts / total_accounts * 100) if total_accounts > 0 else 0
#             )

#             # Calculate collection consistency
#             monthly_rates = []
#             for placement_id in client_placements["placement_id"].unique():
#                 placement = client_placements[
#                     client_placements["placement_id"] == placement_id
#                 ]
#                 placement_loaded = placement["original_upb_loaded"].sum()
#                 if placement_loaded > 0:
#                     placement_collected = self.processed_transactions[
#                         self.processed_transactions["file_number"].isin(
#                             placement["file_number"]
#                         )
#                     ]["payment_amount"].sum()
#                     monthly_rates.append((placement_collected / placement_loaded) * 100)

#             liquidation_std = np.std(monthly_rates) if monthly_rates else 0

#             # Calculate trend
#             if len(monthly_rates) >= 2:
#                 recent_half = monthly_rates[len(monthly_rates) // 2 :]
#                 older_half = monthly_rates[: len(monthly_rates) // 2]
#                 performance_trend = (
#                     np.mean(recent_half) - np.mean(older_half)
#                     if recent_half and older_half
#                     else 0
#                 )
#             else:
#                 performance_trend = 0

#             clients.append(
#                 {
#                     "client_number": client_number,
#                     "total_placements": total_placements,
#                     "total_loaded": round(total_loaded, 2),
#                     "total_collected": round(total_collected, 2),
#                     "total_accounts": total_accounts,
#                     "avg_liquidation": round(avg_liquidation, 2),
#                     "avg_activation": round(avg_activation, 2),
#                     "liquidation_std": round(liquidation_std, 2),
#                     "performance_trend": round(performance_trend, 2),
#                 }
#             )

#         return pd.DataFrame(clients)

#     def render(self):
#         """Render the portfolio performance dashboard"""
#         metrics = self.get_cached()

#         with ui.card().classes("w-full p-6"):
#             ui.label("Portfolio Performance Analysis").classes(
#                 "text-2xl font-bold mb-4"
#             )

#             with ui.tabs().classes("w-full") as tabs:
#                 client_tab = ui.tab("Client Overview")
#                 placement_tab = ui.tab("Placement Analysis")
#                 time_tab = ui.tab("Time Analysis")

#             with ui.tab_panels(tabs, value=client_tab).classes("w-full mt-4"):
#                 with ui.tab_panel(client_tab):
#                     self._render_client_overview(metrics)
#                 with ui.tab_panel(placement_tab):
#                     self._render_placement_analysis(metrics)
#                 with ui.tab_panel(time_tab):
#                     self._render_time_analysis(metrics)

#     def _render_client_overview(self, metrics):
#         """Render client-level performance overview"""
#         if "client_metrics" not in metrics:
#             with ui.card().classes("w-full p-4"):
#                 ui.label("No client metrics available").classes("text-lg")
#                 return

#         client_metrics = pd.DataFrame(metrics["client_metrics"])

#         # Create client performance summary chart with names
#         client_summary = {
#             "chart": {"type": "column"},
#             "title": {"text": "Client Portfolio Performance"},
#             "xAxis": {
#                 "categories": [
#                     self._get_client_name(cn) for cn in client_metrics["client_number"]
#                 ],
#                 "labels": {"rotation": -45},
#             },
#             "yAxis": [
#                 {
#                     "title": {"text": "Amount ($)"},
#                     "labels": {"format": "${value:,.0f}"},
#                 },
#                 {"title": {"text": "Liquidation Rate (%)"}, "opposite": True},
#             ],
#             "series": [
#                 {
#                     "name": "Total Loaded",
#                     "type": "column",
#                     "yAxis": 0,
#                     "data": client_metrics["total_loaded"].tolist(),
#                 },
#                 {
#                     "name": "Liquidation Rate",
#                     "type": "line",
#                     "yAxis": 1,
#                     "data": client_metrics["avg_liquidation"].round(1).tolist(),
#                 },
#             ],
#         }

#         ui.highchart(client_summary).classes("w-full h-64")

#         # Add client metric cards with names
#         with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
#             for _, client in client_metrics.iterrows():
#                 with ui.card().classes("p-4"):
#                     ui.label(self._get_client_name(client["client_number"])).classes(
#                         "text-lg font-bold mb-2"
#                     )
#                     with ui.column().classes("gap-2"):
#                         ui.label(f"Placements: {client['total_placements']}")
#                         ui.label(f"Total Loaded: ${client['total_loaded']:,.2f}")
#                         ui.label(f"Total Collected: ${client['total_collected']:,.2f}")
#                         ui.label(f"Avg Liquidation: {client['avg_liquidation']:.1f}%")
#                         ui.label(
#                             f"Performance Trend: "
#                             f"{'↑' if client['performance_trend'] > 0 else '↓'} "
#                             f"{abs(client['performance_trend']):.1f}%"
#                         )

#     def _render_placement_analysis(self, metrics):
#         """Render detailed placement analysis"""
#         if "placement_metrics" not in metrics:
#             with ui.card().classes("w-full p-4"):
#                 ui.label("No placement metrics available").classes("text-lg")
#                 return

#         placement_metrics = pd.DataFrame(metrics["placement_metrics"])
#         selected_id = placement_metrics["placement_id"].iloc[0]

#         @ui.refreshable
#         def placement_content(selected_placement_id):
#             placement = placement_metrics[
#                 placement_metrics["placement_id"] == selected_placement_id
#             ].iloc[0]

#             # Create monthly collections chart
#             collections_chart = {
#                 "chart": {"type": "column"},
#                 "title": {
#                     "text": f"Monthly Collections - {self._get_client_name(placement['client_number'])}"
#                 },
#                 "xAxis": {"categories": [f"Month {i+1}" for i in range(12)]},
#                 "yAxis": [
#                     {
#                         "title": {"text": "Amount ($)"},
#                         "labels": {"format": "${value:,.0f}"},
#                     },
#                     {
#                         "title": {"text": "% of Total"},
#                         "opposite": True,
#                         "labels": {"format": "{value}%"},
#                     },
#                 ],
#                 "series": [
#                     {
#                         "name": "Monthly Collection",
#                         "type": "column",
#                         "data": placement["monthly_collections"],
#                     },
#                     {
#                         "name": "% of Total",
#                         "type": "line",
#                         "yAxis": 1,
#                         "data": [
#                             (
#                                 round((x / placement["total_collected"] * 100), 2)
#                                 if placement["total_collected"] > 0
#                                 else 0
#                             )
#                             for x in placement["monthly_collections"]
#                         ],
#                     },
#                 ],
#             }

#             ui.highchart(collections_chart).classes("w-full h-64")

#             # Add placement details
#             with ui.grid(columns=2).classes("w-full gap-6 mt-6"):
#                 # Performance Metrics Card
#                 with ui.card().classes("p-4"):
#                     ui.label("Performance Metrics").classes("text-lg font-bold mb-2")
#                     with ui.column().classes("gap-2"):
#                         ui.label(f"Total Loaded: ${placement['total_loaded']:,.2f}")
#                         ui.label(
#                             f"Total Collected: ${placement['total_collected']:,.2f}"
#                         )
#                         ui.label(
#                             f"Liquidation Rate: {placement['liquidation_rate']:.2f}%"
#                         )
#                         ui.label(f"Account Count: {placement['account_count']}")
#                         ui.label(
#                             f"Activation Rate: {placement['activation_rate']:.2f}%"
#                         )
#                         avg_per_account = (
#                             placement["total_collected"] / placement["account_count"]
#                             if placement["account_count"] > 0
#                             else 0
#                         )
#                         ui.label(
#                             f"Average Per Account: ${round(avg_per_account, 2):,.2f}"
#                         )

#                 # Payment Analysis Card
#                 with ui.card().classes("p-4"):
#                     ui.label("Payment Analysis").classes("text-lg font-bold mb-2")
#                     with ui.column().classes("gap-2"):
#                         # Calculate payment frequency
#                         total_months_with_payments = sum(
#                             1 for x in placement["monthly_collections"] if x > 0
#                         )
#                         ui.label(f"Active Payment Months: {total_months_with_payments}")

#                         # Calculate payment consistency
#                         payment_months = [
#                             i + 1
#                             for i, x in enumerate(placement["monthly_collections"])
#                             if x > 0
#                         ]
#                         avg_gap = (
#                             round(np.mean(np.diff(payment_months)), 2)
#                             if len(payment_months) > 1
#                             else 0
#                         )
#                         ui.label(f"Average Months Between Payments: {avg_gap}")

#                         # Best and worst months
#                         best_month = max(
#                             enumerate(placement["monthly_collections"], 1),
#                             key=lambda x: x[1],
#                         )
#                         ui.label(
#                             f"Best Month: Month {best_month[0]} "
#                             f"(${round(best_month[1], 2):,.2f})"
#                         )

#                         # Calculate payment distribution
#                         q1, q2, q3 = (
#                             np.percentile(
#                                 [x for x in placement["monthly_collections"] if x > 0],
#                                 [25, 50, 75],
#                             )
#                             if any(x > 0 for x in placement["monthly_collections"])
#                             else (0, 0, 0)
#                         )

#                         ui.label(f"Median Monthly Payment: ${round(q2, 2):,.2f}")
#                         ui.label(
#                             f"Payment Range: ${round(q1, 2):,.2f} - ${round(q3, 2):,.2f}"
#                         )

#         # Create sorted placement options
#         placement_data = [
#             {
#                 "id": p,
#                 "client_number": c,
#                 "client_name": self._get_client_name(c),
#                 "date": pd.to_datetime(d),
#                 "display_date": pd.to_datetime(d).strftime("%Y-%m"),
#             }
#             for p, c, d in zip(
#                 placement_metrics["placement_id"],
#                 placement_metrics["client_number"],
#                 placement_metrics["placement_date"],
#             )
#         ]

#         # Sort by client name and then by date descending
#         sorted_placements = sorted(
#             placement_data, key=lambda x: (x["client_name"], -x["date"].timestamp())
#         )

#         # Create selector with sorted options
#         def on_select(e):
#             nonlocal selected_id
#             selected_id = e.value
#             placement_content.refresh(selected_id)

#         ui.select(
#             options={
#                 p["id"]: f"{p['client_name']} - {p['display_date']}"
#                 for p in sorted_placements
#             },
#             value=selected_id,
#             label="Select Placement",
#             on_change=on_select,
#         ).classes("w-full mb-4")

#         placement_content(selected_id)

#     def _render_time_analysis(self, metrics):
#         """Render time-based analysis showing trends and patterns"""
#         if not metrics.get("placement_metrics"):
#             with ui.card().classes("w-full p-4"):
#                 ui.label("No time analysis metrics available").classes("text-lg")
#                 return

#         placement_metrics = pd.DataFrame(metrics["placement_metrics"])

#         # Monthly trend analysis
#         monthly_data = placement_metrics.copy()
#         monthly_data["month_year"] = pd.to_datetime(
#             monthly_data["placement_date"]
#         ).dt.strftime("%Y-%m")
#         monthly_stats = (
#             monthly_data.groupby("month_year")
#             .agg(
#                 {
#                     "total_loaded": lambda x: round(sum(x), 2),
#                     "total_collected": lambda x: round(sum(x), 2),
#                     "liquidation_rate": lambda x: round(np.mean(x), 2),
#                     "activation_rate": lambda x: round(np.mean(x), 2),
#                 }
#             )
#             .reset_index()
#         )
#         monthly_stats = monthly_stats.sort_values("month_year")

#         # Create monthly trend chart
#         trend_chart = {
#             "chart": {"type": "line"},
#             "title": {"text": "Monthly Performance Trends"},
#             "xAxis": {
#                 "categories": monthly_stats["month_year"].tolist(),
#                 "title": {"text": "Month"},
#                 "labels": {"rotation": -45},
#             },
#             "yAxis": [
#                 {"title": {"text": "Rate (%)"}, "min": 0, "max": 100},
#                 {
#                     "title": {"text": "Amount ($)"},
#                     "opposite": True,
#                     "labels": {"format": "${value:,.0f}"},
#                 },
#             ],
#             "series": [
#                 {
#                     "name": "Liquidation Rate",
#                     "type": "line",
#                     "data": [
#                         round(x, 2) for x in monthly_stats["liquidation_rate"].tolist()
#                     ],
#                     "yAxis": 0,
#                 },
#                 {
#                     "name": "Activation Rate",
#                     "type": "line",
#                     "data": [
#                         round(x, 2) for x in monthly_stats["activation_rate"].tolist()
#                     ],
#                     "yAxis": 0,
#                 },
#                 {
#                     "name": "Total Loaded",
#                     "type": "column",
#                     "data": [
#                         round(x, 2) for x in monthly_stats["total_loaded"].tolist()
#                     ],
#                     "yAxis": 1,
#                 },
#             ],
#         }

#         ui.highchart(trend_chart).classes("w-full h-64")

#         # Seasonal pattern analysis
#         seasonal_data = placement_metrics.copy()
#         seasonal_data["month"] = pd.to_datetime(
#             seasonal_data["placement_date"]
#         ).dt.month
#         seasonal_stats = (
#             seasonal_data.groupby("month")
#             .agg(
#                 {
#                     "liquidation_rate": [
#                         lambda x: round(np.mean(x), 2),
#                         lambda x: round(np.std(x), 2),
#                     ],
#                     "activation_rate": lambda x: round(np.mean(x), 2),
#                     "total_collected": lambda x: round(np.mean(x), 2),
#                 }
#             )
#             .reset_index()
#         )
#         seasonal_stats.columns = [
#             "month",
#             "avg_liquidation",
#             "liquidation_std",
#             "avg_activation",
#             "avg_collected",
#         ]

#         # Create seasonal pattern chart
#         seasonal_chart = {
#             "chart": {"type": "arearange"},
#             "title": {"text": "Seasonal Performance Patterns"},
#             "xAxis": {
#                 "categories": [
#                     "Jan",
#                     "Feb",
#                     "Mar",
#                     "Apr",
#                     "May",
#                     "Jun",
#                     "Jul",
#                     "Aug",
#                     "Sep",
#                     "Oct",
#                     "Nov",
#                     "Dec",
#                 ]
#             },
#             "yAxis": {"title": {"text": "Liquidation Rate (%)"}},
#             "series": [
#                 {
#                     "name": "Liquidation Range",
#                     "type": "arearange",
#                     "data": [
#                         [
#                             round(
#                                 float(row["avg_liquidation"] - row["liquidation_std"]),
#                                 2,
#                             ),
#                             round(
#                                 float(row["avg_liquidation"] + row["liquidation_std"]),
#                                 2,
#                             ),
#                         ]
#                         for _, row in seasonal_stats.iterrows()
#                     ],
#                     "color": "rgba(124, 181, 236, 0.3)",
#                 },
#                 {
#                     "name": "Average Liquidation",
#                     "type": "line",
#                     "data": [
#                         round(x, 2) for x in seasonal_stats["avg_liquidation"].tolist()
#                     ],
#                     "marker": {"enabled": True},
#                 },
#             ],
#         }

#         ui.highchart(seasonal_chart).classes("w-full h-64 mt-6")

#         # Add analysis cards
#         with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
#             # Trend Analysis Card
#             with ui.card().classes("p-4"):
#                 ui.label("Trend Analysis").classes("text-lg font-bold mb-2")
#                 recent_months = monthly_stats.tail(3)
#                 with ui.column().classes("gap-2"):
#                     ui.label("Last 3 Months:")
#                     for _, month in recent_months.iterrows():
#                         ui.label(
#                             f"{month['month_year']}: "
#                             f"{round(month['liquidation_rate'], 2)}% liquidation"
#                         )

#             # Seasonal Insights Card
#             with ui.card().classes("p-4"):
#                 ui.label("Seasonal Insights").classes("text-lg font-bold mb-2")
#                 best_month = seasonal_stats.loc[
#                     seasonal_stats["avg_liquidation"].idxmax()
#                 ]
#                 worst_month = seasonal_stats.loc[
#                     seasonal_stats["avg_liquidation"].idxmin()
#                 ]
#                 with ui.column().classes("gap-2"):
#                     ui.label(
#                         f"Best Month: {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(best_month['month'])-1]}"
#                     )
#                     ui.label(f"Peak Rate: {round(best_month['avg_liquidation'], 2)}%")
#                     ui.label(
#                         f"Worst Month: {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(worst_month['month'])-1]}"
#                     )
#                     ui.label(f"Low Rate: {round(worst_month['avg_liquidation'], 2)}%")

#             # Performance Stability Card
#             with ui.card().classes("p-4"):
#                 ui.label("Performance Stability").classes("text-lg font-bold mb-2")
#                 overall_std = round(seasonal_stats["liquidation_std"].mean(), 2)
#                 with ui.column().classes("gap-2"):
#                     ui.label(f"Average Volatility: {overall_std}%")
#                     ui.label(
#                         f"Most Stable Month: "
#                         f"{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(seasonal_stats.loc[seasonal_stats['liquidation_std'].idxmin(), 'month'])-1]}"
#                     )
#                     ui.label(
#                         f"Most Variable Month: "
#                         f"{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][int(seasonal_stats.loc[seasonal_stats['liquidation_std'].idxmax(), 'month'])-1]}"
#                     )


# def create_portfolio_performance_widget(
#     widget_configuration: dict = None, force_refresh=False
# ):
#     """
#     Factory function to create a new PortfolioPerformanceWidget instance

#     Args:
#         widget_configuration (dict, optional): Configuration dictionary for the widget.
#             If not provided, uses default configuration.
#         force_refresh (bool, optional): Force refresh of data regardless of cache state.
#     """
#     if widget_configuration is None:
#         widget_configuration = {
#             "required_datasets": ["accounts", "transactions", "contacts"],
#             "company_id": "ALL",
#             "widget_id": "wgt_portfolio_performance",
#             "force_refresh": force_refresh,
#         }
#     return PortfolioPerformanceWidget(widget_configuration)
