# from nicegui import ui
# import pandas as pd
# import numpy as np
# from datetime import datetime
# from .WidgetFramework import WidgetFramework


# class RiskScoringWidget(WidgetFramework):
#     def __init__(self, widget_configuration: dict):
#         super().__init__(widget_configuration)
#         self.force_refresh = False
#         if self.is_recalc_needed():
#             self._calculate_metrics()

#     def _calculate_transaction_weights(self, file_number, transactions_df, current_upb):
#         """Calculate weight based on payments relative to current balance"""
#         if current_upb == 0:
#             return 0

#         account_payments = transactions_df[
#             transactions_df["file_number"] == file_number
#         ]["payment_amount"]

#         if len(account_payments) == 0:
#             return 0

#         payment_weights = [(payment / current_upb) for payment in account_payments]
#         return sum(payment_weights) / len(payment_weights)

#     def _calculate_tu_score_risk(self, tu_score):
#         """Convert TU score (400-850) to risk score (0-1)"""
#         if pd.isna(tu_score) or tu_score == 0:
#             return 0.5

#         normalized = (tu_score - 400) / (850 - 400)
#         return 1 - normalized

#     def _calculate_call_risk(self, file_number, outbound_df):
#         """Calculate call risk based on success ratio, volume, and recency"""
#         account_calls = outbound_df[outbound_df["file_number"] == file_number]

#         if len(account_calls) == 0:
#             return 1.0

#         successful_calls = account_calls["agent_id"].notna().sum()
#         success_ratio = successful_calls / len(account_calls)

#         max_calls = 10
#         volume_score = min(len(account_calls) / max_calls, 1)

#         latest_call = pd.to_datetime(
#             account_calls[
#                 [
#                     "call_completed_date_year",
#                     "call_completed_date_month",
#                     "call_completed_date_day",
#                 ]
#             ]
#             .astype(str)
#             .agg("-".join, axis=1)
#         ).max()

#         days_since_call = (pd.Timestamp.now() - latest_call).days
#         recency_score = min(days_since_call / 30, 1)

#         return (
#             (1 - success_ratio) * 0.4 + (1 - volume_score) * 0.3 + recency_score * 0.3
#         )

#     def _calculate_final_risk_score(self, row):
#         """Calculate final risk score based on weighted factors"""
#         weights = {"transaction_weight": 0.35, "tu_risk": 0.35, "call_risk": 0.30}

#         risk_score = sum(row[factor] * weight for factor, weight in weights.items())
#         return min(max(risk_score, 0), 1)

#     def _calculate_metrics(self):
#         """Calculate risk scores and segments"""
#         accounts_df = self.get_accounts()
#         transactions_df = self.get_transactions()
#         outbound_df = self.get_outbound()

#         risk_data = []

#         for _, account in accounts_df.iterrows():
#             file_number = account["file_number"]
#             current_upb = account["current_upb"]
#             tu_score = account["tu_score"]

#             transaction_weight = self._calculate_transaction_weights(
#                 file_number, transactions_df, current_upb
#             )

#             tu_risk = self._calculate_tu_score_risk(tu_score)

#             call_risk = self._calculate_call_risk(file_number, outbound_df)

#             row_data = {
#                 "file_number": file_number,
#                 "transaction_weight": transaction_weight,
#                 "tu_risk": tu_risk,
#                 "call_risk": call_risk,
#             }

#             row_data["risk_score"] = self._calculate_final_risk_score(row_data)
#             risk_data.append(row_data)

#         risk_df = pd.DataFrame(risk_data)

#         # Calculate summary metrics
#         summary = {
#             "avg_risk_score": float(risk_df["risk_score"].mean()),
#             "high_risk_count": len(risk_df[risk_df["risk_score"] > 0.7]),
#             "medium_risk_count": len(
#                 risk_df[(risk_df["risk_score"] > 0.3) & (risk_df["risk_score"] <= 0.7)]
#             ),
#             "low_risk_count": len(risk_df[risk_df["risk_score"] <= 0.3]),
#         }

#         # First, store the summary and metadata
#         base_metrics = {
#             "summary": summary,
#             "total_chunks": 0,  # Will be updated after chunking
#             "last_modified": int(datetime.now().timestamp()),
#         }
#         self.update_metric_cache(base_metrics)

#         # Then store the data in chunks
#         CHUNK_SIZE = 100
#         for i in range(0, len(risk_data), CHUNK_SIZE):
#             chunk = risk_data[i : i + CHUNK_SIZE]
#             chunk_metrics = {
#                 f"risk_data_chunk_{i//CHUNK_SIZE}": chunk,
#                 "total_chunks": (len(risk_data) + CHUNK_SIZE - 1) // CHUNK_SIZE,
#             }
#             self.update_metric_cache(chunk_metrics)

#     def get_cached(self):
#         """Override get_cached to handle chunked data"""
#         try:
#             if self.force_refresh:
#                 self._calculate_metrics()

#             cached_data = super().get_cached()
#             if not cached_data or "summary" not in cached_data:
#                 return {}

#             # Initialize complete data with base metrics
#             complete_data = {
#                 "risk_data": [],
#                 "summary": cached_data["summary"],
#                 "last_modified": cached_data.get("last_modified", 0),
#             }

#             # If data is chunked, reconstruct it
#             total_chunks = cached_data.get("total_chunks", 0)
#             if total_chunks > 0:
#                 for i in range(total_chunks):
#                     chunk_key = f"risk_data_chunk_{i}"
#                     if chunk_key in cached_data:
#                         complete_data["risk_data"].extend(cached_data[chunk_key])

#             return complete_data
#         except Exception as e:
#             print(f"Error in get_cached: {str(e)}")
#             return {
#                 "summary": {
#                     "avg_risk_score": 0.0,
#                     "high_risk_count": 0,
#                     "medium_risk_count": 0,
#                     "low_risk_count": 0,
#                 },
#                 "risk_data": [],
#             }

#     def render(self):
#         """Render the risk scoring dashboard"""
#         metrics = self.get_cached()

#         with ui.card().classes("w-full p-6"):
#             ui.label("Risk Scoring Analysis").classes("text-2xl font-bold mb-4")

#             with ui.tabs().classes("w-full") as tabs:
#                 overview_tab = ui.tab("Overview")
#                 details_tab = ui.tab("Risk Details")

#             with ui.tab_panels(tabs, value=overview_tab).classes("w-full mt-4"):
#                 with ui.tab_panel(overview_tab):
#                     self._render_overview(metrics)
#                 with ui.tab_panel(details_tab):
#                     self._render_details(metrics)

#     def _render_overview(self, metrics):
#         """Render overview panel"""
#         summary = metrics["summary"]

#         # Create distribution chart
#         distribution_data = {
#             "chart": {"type": "pie"},
#             "title": {"text": "Risk Distribution"},
#             "series": [
#                 {
#                     "name": "Accounts",
#                     "data": [
#                         ["High Risk", summary["high_risk_count"]],
#                         ["Medium Risk", summary["medium_risk_count"]],
#                         ["Low Risk", summary["low_risk_count"]],
#                     ],
#                 }
#             ],
#         }

#         ui.highchart(distribution_data).classes("w-full h-64")

#         with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
#             with ui.card().classes("p-4"):
#                 ui.label("Average Risk Score").classes("text-lg font-bold mb-2")
#                 ui.label(f"{summary['avg_risk_score']:.2f}").classes("text-xl")

#             with ui.card().classes("p-4"):
#                 ui.label("High Risk Accounts").classes("text-lg font-bold mb-2")
#                 ui.label(f"{summary['high_risk_count']:,}").classes(
#                     "text-xl text-red-600"
#                 )

#             with ui.card().classes("p-4"):
#                 ui.label("Low Risk Accounts").classes("text-lg font-bold mb-2")
#                 ui.label(f"{summary['low_risk_count']:,}").classes(
#                     "text-xl text-green-600"
#                 )

#     def _render_details(self, metrics):
#         """Render details panel"""
#         try:
#             if not metrics or "risk_data" not in metrics or not metrics["risk_data"]:
#                 with ui.card().classes("w-full p-4"):
#                     ui.label("No risk data available").classes("text-lg")
#                 return

#             risk_df = pd.DataFrame(metrics["risk_data"])
#             if risk_df.empty:
#                 with ui.card().classes("w-full p-4"):
#                     ui.label("No risk data available").classes("text-lg")
#                 return

#             # Create risk factors chart
#             factors_data = {
#                 "chart": {"type": "column"},
#                 "title": {"text": "Risk Factor Distribution"},
#                 "xAxis": {"categories": ["Transaction", "Credit", "Contact"]},
#                 "yAxis": {"title": {"text": "Average Risk Score"}},
#                 "series": [
#                     {
#                         "name": "Risk Factors",
#                         "data": [
#                             float(
#                                 risk_df["transaction_weight"].mean()
#                                 if "transaction_weight" in risk_df
#                                 else 0
#                             ),
#                             float(
#                                 risk_df["tu_risk"].mean() if "tu_risk" in risk_df else 0
#                             ),
#                             float(
#                                 risk_df["call_risk"].mean()
#                                 if "call_risk" in risk_df
#                                 else 0
#                             ),
#                         ],
#                     }
#                 ],
#             }

#             ui.highchart(factors_data).classes("w-full h-64")

#             # Add detailed breakdown
#             with ui.grid(columns=3).classes("w-full gap-6 mt-6"):
#                 # Transaction Risk Card
#                 with ui.card().classes("p-4"):
#                     ui.label("Transaction Risk").classes("text-lg font-bold mb-2")
#                     if "transaction_weight" in risk_df:
#                         avg_trans = risk_df["transaction_weight"].mean()
#                         high_trans = len(risk_df[risk_df["transaction_weight"] > 0.7])
#                         ui.label(f"Average: {avg_trans:.2f}")
#                         ui.label(f"High Risk Count: {high_trans}")
#                     else:
#                         ui.label("No transaction data available")

#                 # Credit Risk Card
#                 with ui.card().classes("p-4"):
#                     ui.label("Credit Risk").classes("text-lg font-bold mb-2")
#                     if "tu_risk" in risk_df:
#                         avg_credit = risk_df["tu_risk"].mean()
#                         high_credit = len(risk_df[risk_df["tu_risk"] > 0.7])
#                         ui.label(f"Average: {avg_credit:.2f}")
#                         ui.label(f"High Risk Count: {high_credit}")
#                     else:
#                         ui.label("No credit data available")

#                 # Contact Risk Card
#                 with ui.card().classes("p-4"):
#                     ui.label("Contact Risk").classes("text-lg font-bold mb-2")
#                     if "call_risk" in risk_df:
#                         avg_contact = risk_df["call_risk"].mean()
#                         high_contact = len(risk_df[risk_df["call_risk"] > 0.7])
#                         ui.label(f"Average: {avg_contact:.2f}")
#                         ui.label(f"High Risk Count: {high_contact}")
#                     else:
#                         ui.label("No contact data available")

#         except Exception as e:
#             print(f"Error rendering details: {str(e)}")
#             with ui.card().classes("w-full p-4"):
#                 ui.label("Error displaying risk details").classes("text-lg")


# def create_risk_scoring_widget(
#     widget_configuration: dict = None, force_refresh: bool = False
# ):
#     """Factory function to create a new RiskScoringWidget instance"""
#     if widget_configuration is None:
#         widget_configuration = {
#             "required_datasets": ["accounts", "transactions", "contacts", "outbound"],
#             "company_id": "ALL",
#             "widget_id": "wgt_risk_scoring",
#             "force_refresh": force_refresh,
#         }
#     return RiskScoringWidget(widget_configuration)
