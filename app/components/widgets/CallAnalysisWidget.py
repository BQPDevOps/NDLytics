from nicegui import ui
import pandas as pd
from datetime import datetime
from .WidgetFramework import WidgetFramework
from modules import ListManager


class CallAnalysisWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _calculate_metrics(self):
        """Calculate all metrics and cache them"""
        try:
            outbound_df = self.get_outbound()

            # Daily distribution calculation
            day_columns = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            daily_dist = {
                day.capitalize(): int(outbound_df[day].sum()) for day in day_columns
            }

            metrics = {
                "call_volume": {
                    "total_calls": int(outbound_df["total_calls"].sum()),
                    "daily_distribution": daily_dist,
                    "cost_metrics": {
                        "average_cost": float(
                            outbound_df["delivery_cost_average"].mean()
                        ),
                        "total_cost": float(outbound_df["delivery_cost_sum"].sum()),
                    },
                },
                "interaction_outcomes": {
                    "types": {
                        col.replace("interaction_", ""): float(outbound_df[col].mean())
                        for col in outbound_df.columns
                        if col.startswith("interaction_")
                    },
                    "results": {
                        col.replace("result_", ""): float(outbound_df[col].mean())
                        for col in outbound_df.columns
                        if col.startswith("result_")
                    },
                },
                "contact_channels": {
                    "phone_distribution": {
                        "cell": int(outbound_df["phone_cell_count"].sum()),
                        "home": int(outbound_df["phone_home_count"].sum()),
                        "work": int(outbound_df["phone_work_count"].sum()),
                        "other": int(outbound_df["phone_other_count"].sum()),
                    }
                },
                "agent_performance": {
                    "agent_stats": {
                        col.replace("agent_id_", ""): float(outbound_df[col].sum())
                        for col in outbound_df.columns
                        if col.startswith("agent_id_")
                    }
                },
                "last_modified": int(datetime.now().timestamp()),
            }

            self.update_metric_cache(metrics)

        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            self.update_metric_cache(
                {
                    "call_volume": {},
                    "interaction_outcomes": {},
                    "contact_channels": {},
                    "agent_performance": {},
                    "last_modified": int(datetime.now().timestamp()),
                }
            )

    def render(self):
        """Render the call analysis dashboard"""
        metrics = self.get_cached()

        with ui.card().classes("w-full p-6 max-h-[76vh]"):
            with ui.row().classes("flex justify-between items-center gap-4 w-full"):
                ui.label("Outbound Call Performance (Lifetime)").classes(
                    "text-2xl font-bold"
                )
                ui.button(
                    icon="refresh",
                    on_click=lambda: [self._calculate_metrics(), self.render()],
                ).props("round flat")

            with ui.tabs().classes("w-full") as tabs:
                volume_tab = ui.tab("Call Volume")
                outcomes_tab = ui.tab("Outcomes")
                channels_tab = ui.tab("Contact Channels")
                agents_tab = ui.tab("Agent Performance")

            with ui.tab_panels(tabs, value=volume_tab).classes("w-full mt-4"):
                with ui.tab_panel(volume_tab):
                    self._render_volume_analysis(metrics)

                with ui.tab_panel(outcomes_tab):
                    self._render_outcomes_analysis(metrics)

                with ui.tab_panel(channels_tab):
                    self._render_channels_analysis(metrics)

                with ui.tab_panel(agents_tab):
                    self._render_agent_analysis(metrics)

    def _render_volume_analysis(self, metrics):
        if not metrics.get("call_volume"):
            ui.label("No call volume data available").classes("text-lg")
            return

        call_volume = metrics["call_volume"]
        daily_dist = call_volume["daily_distribution"]

        ordered_days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        ordered_data = [daily_dist[day] for day in ordered_days]

        chart_data = {
            "chart": {"type": "column"},
            "title": {"text": "Call Volume by Day of Week"},
            "xAxis": {"categories": ordered_days},
            "yAxis": {"title": {"text": "Number of Calls"}},
            "series": [{"name": "Calls", "data": ordered_data}],
        }

        ui.highchart(chart_data).classes("w-full h-64")

        with ui.grid(columns=3).classes("w-full gap-6 mt-4"):
            metrics_cards = [
                ("Total Calls", f"{call_volume['total_calls']:,}"),
                ("Average Cost", f"${call_volume['cost_metrics']['average_cost']:.2f}"),
                ("Total Cost", f"${call_volume['cost_metrics']['total_cost']:,.2f}"),
            ]

            for label, value in metrics_cards:
                with ui.card().classes("p-4"):
                    ui.label(label).classes("text-lg font-bold")
                    ui.label(value)

    def _render_outcomes_analysis(self, metrics):
        if not metrics.get("interaction_outcomes"):
            ui.label("No outcome data available").classes("text-lg")
            return

        outcomes = metrics["interaction_outcomes"]

        interaction_chart = {
            "chart": {"type": "pie"},
            "title": {"text": "Call Interaction Types"},
            "series": [
                {
                    "name": "Percentage",
                    "data": [
                        {"name": k, "y": v * 100} for k, v in outcomes["types"].items()
                    ],
                }
            ],
        }

        results_chart = {
            "chart": {"type": "column"},
            "title": {"text": "Call Results"},
            "xAxis": {"categories": list(outcomes["results"].keys())},
            "yAxis": {"title": {"text": "Success Rate (%)"}},
            "series": [
                {
                    "name": "Success Rate",
                    "data": [v * 100 for v in outcomes["results"].values()],
                }
            ],
        }

        with ui.grid(columns=2).classes("w-full gap-6"):
            ui.highchart(interaction_chart).classes("w-full h-64")
            ui.highchart(results_chart).classes("w-full h-64")

    def _render_channels_analysis(self, metrics):
        if not metrics.get("contact_channels"):
            ui.label("No channel data available").classes("text-lg")
            return

        channels = metrics["contact_channels"]["phone_distribution"]

        chart_data = {
            "chart": {"type": "pie"},
            "title": {"text": "Phone Number Distribution"},
            "series": [
                {
                    "name": "Count",
                    "data": [{"name": k.title(), "y": v} for k, v in channels.items()],
                }
            ],
        }

        ui.highchart(chart_data).classes("w-full h-64")

        total = sum(channels.values())
        with ui.grid(columns=4).classes("w-full gap-4 mt-4"):
            for channel, count in channels.items():
                with ui.card().classes("p-4"):
                    percentage = (count / total * 100) if total > 0 else 0
                    ui.label(channel.title()).classes("font-bold")
                    ui.label(f"Count: {count:,}")
                    ui.label(f"Percentage: {percentage:.1f}%")

    def _render_agent_analysis(self, metrics):
        if not metrics.get("agent_performance"):
            ui.label("No agent performance data available").classes("text-lg")
            return

        agent_stats = metrics["agent_performance"]["agent_stats"]
        list_manager = ListManager()
        operator_list = list_manager.get_list("operator_list")

        # Map agent IDs to names
        agent_stats_named = {}
        tcn_total = 0

        for agent_id, value in agent_stats.items():
            clean_id = str(int(float(agent_id)))  # Remove .0 and convert to string
            if clean_id in operator_list:
                agent_name = operator_list[clean_id]
                agent_stats_named[agent_name] = value
            else:
                tcn_total += value

        if tcn_total > 0:
            agent_stats_named["TCN"] = tcn_total

        chart_data = {
            "chart": {"type": "bar"},
            "title": {"text": "Agent Call Volume"},
            "xAxis": {"categories": list(agent_stats_named.keys())},
            "yAxis": {"title": {"text": "Number of Calls"}},
            "series": [
                {"name": "Calls Handled", "data": list(agent_stats_named.values())}
            ],
        }

        ui.highchart(chart_data).classes("w-full h-64")


def create_call_analysis_widget(widget_configuration: dict = None, force_refresh=False):
    """Factory function to create a new CallAnalysisWidget instance."""
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["outbound"],
            "company_id": "ALL",
            "widget_id": "wgt_call_analysis",
            "force_refresh": force_refresh,
        }
    return CallAnalysisWidget(widget_configuration)
