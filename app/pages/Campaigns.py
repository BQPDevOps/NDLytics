from datetime import datetime

from nicegui import ui
import pandas as pd
import numpy as np

from components.shared import StaticPage
from components.common import MiniGridCard
from utils.helpers import tcn_adapter
from theme import ThemeManager


class ComprehensiveCallAnalysis:
    def __init__(self, df):
        self.df = df
        self.prepare_data()
        self.theme_manager = ThemeManager()

    def prepare_data(self):
        # Convert date and time columns
        self.df["Call DateTime"] = pd.to_datetime(
            self.df["Call Date"] + " " + self.df["Call Start Time"]
        )
        self.df["Call Duration"] = pd.to_timedelta(self.df["Call Duration"])

        # Calculate additional metrics
        self.df["5min_interval"] = self.df["Call DateTime"].dt.floor("5min")
        self.df["Is Successful"] = self.df["Result"].isin(
            ["Payment Made", "Payment Plan", "Promise To Pay"]
        )

        # Create Score Ranges
        self.df["Score Range"] = pd.cut(
            self.df["Score"],
            bins=[0, 500, 600, 700, 800, 850],
            labels=["0-500", "501-600", "601-700", "701-800", "801-850"],
        )

    def render(self):
        with ui.card().classes("w-full p-4"):
            with ui.tabs().classes("w-full") as tabs:
                ui.tab("Overview")
                ui.tab("Time Analysis")
                ui.tab("Performance Metrics")
                ui.tab("Call Outcome Analysis")

            with ui.tab_panels(tabs, value="Overview").classes("w-full"):
                with ui.tab_panel("Overview"):
                    self.render_overview()

                with ui.tab_panel("Time Analysis"):
                    self.render_time_analysis()

                with ui.tab_panel("Performance Metrics"):
                    self.render_performance_metrics()

                with ui.tab_panel("Call Outcome Analysis"):
                    self.render_call_outcome_analysis()

    def render_overview(self):
        total_calls = len(self.df)
        unique_clients = self.df["Client Name"].nunique()
        avg_duration = self.df["Call Duration"].mean()
        success_rate = (self.df["Is Successful"].sum() / total_calls) * 100

        with ui.grid(columns=4).classes("w-full"):
            self.create_stat_card("Total Calls", total_calls)
            self.create_stat_card("Unique Clients", unique_clients)
            self.create_stat_card(
                "Avg Call Duration", f"{avg_duration.total_seconds() / 60:.2f} min"
            )
            self.create_stat_card("Success Rate", f"{success_rate:.2f}%")

        with ui.row().classes("w-full mt-4"):
            with ui.column().style("display:flex;flex:1"):
                ui.label("Top 5 TCN Short Codes").classes("text-h6")
                top_short_codes = self.df["TCN Short"].value_counts().head()
                self.create_bar_chart(top_short_codes, "TCN Short Codes")

            with ui.column().style("display:flex;flex:1"):
                ui.label("Top 5 Results").classes("text-h6")
                top_results = self.df["Result"].value_counts().head()
                self.create_bar_chart(top_results, "Results")

    def render_time_analysis(self):
        with ui.row().classes("w-full"):
            with ui.column().style("display:flex;flex:1"):
                ui.label("Calls by 5-Minute Interval").classes("text-h6")
                calls_by_interval = self.df["5min_interval"].value_counts().sort_index()
                self.create_line_chart(calls_by_interval, "Time", "Number of Calls")

            with ui.column().style("display:flex;flex:1"):
                ui.label("Call Duration Distribution").classes("text-h6")
                duration_bins = pd.cut(
                    self.df["Call Duration"].dt.total_seconds() / 60,
                    bins=[0, 1, 2, 3, 5, 10, float("inf")],
                    labels=["0-1", "1-2", "2-3", "3-5", "5-10", "10+"],
                )
                duration_dist = duration_bins.value_counts().sort_index()
                self.create_bar_chart(
                    duration_dist, "Duration (minutes)", "Number of Calls"
                )

    def render_performance_metrics(self):
        with ui.row().classes("w-full"):
            with ui.column().style("display:flex;flex:1"):
                ui.label("Calls Answered by Agent").classes("text-h6")
                calls_by_agent = self.df["Agent ID"].value_counts()
                self.create_bar_chart(calls_by_agent, "Agent ID", "Number of Calls")

            with ui.column().style("display:flex;flex:1"):
                ui.label("Average Call Duration by Result").classes("text-h6")
                avg_duration = (
                    self.df.groupby("Result")["Call Duration"]
                    .mean()
                    .sort_values(ascending=False)
                )
                avg_duration = avg_duration.apply(
                    lambda x: x.total_seconds() / 60
                )  # Convert to minutes
                self.create_bar_chart(
                    avg_duration, "Result", "Average Duration (minutes)"
                )

    def render_call_outcome_analysis(self):
        with ui.row().classes("w-full"):
            with ui.column().style("display:flex;flex:1"):
                ui.label("Call Outcomes by Interaction").classes("text-h6")
                outcome_by_interaction = pd.crosstab(
                    self.df["Interaction"], self.df["Result"]
                )
                self.create_stacked_bar_chart(
                    outcome_by_interaction, "Interaction", "Count"
                )

            with ui.column().style("display:flex;flex:1"):
                ui.label("ANL Count by Score Range").classes("text-h6")
                anl_by_score = (
                    self.df[self.df["TCN Short"] == "ANL"]["Score Range"]
                    .value_counts()
                    .sort_index()
                )
                self.create_bar_chart(anl_by_score, "Score Range", "ANL Count")

    def create_stat_card(self, title, value):
        with ui.card().tight().classes("items-center justify-center w-full gap-0"):
            with ui.row().classes(
                f"w-full items-center justify-center bg-[{self.theme_manager.get_color('primary', 'highlight')}]"
            ):
                ui.label(title).classes("text-subtitle2 text-white")
            with ui.row().classes("w-full items-center justify-center"):
                ui.label(str(value)).classes("text-h6")

    def create_bar_chart(self, data, x_label, y_label="Count"):
        ui.highchart(
            {
                "chart": {"type": "bar"},
                "title": {"text": ""},
                "xAxis": {"categories": data.index.tolist()},
                "yAxis": {"title": {"text": y_label}},
                "series": [{"name": y_label, "data": data.values.tolist()}],
            }
        ).classes("w-full h-64")

    def create_line_chart(self, data, x_label, y_label):
        ui.highchart(
            {
                "chart": {"type": "line"},
                "title": {"text": ""},
                "xAxis": {
                    "categories": [str(x) for x in data.index.tolist()],
                    "title": {"text": x_label},
                },
                "yAxis": {"title": {"text": y_label}},
                "series": [{"name": y_label, "data": data.values.tolist()}],
            }
        ).classes("w-full h-64")

    def create_stacked_bar_chart(self, data, x_label, y_label):
        ui.highchart(
            {
                "chart": {"type": "bar"},
                "title": {"text": ""},
                "xAxis": {"categories": data.index.tolist()},
                "yAxis": {"title": {"text": y_label}},
                "plotOptions": {"series": {"stacking": "normal"}},
                "series": [
                    {"name": col, "data": data[col].values.tolist()}
                    for col in data.columns
                ],
            }
        ).classes("w-full h-64")


class CampaignsPage(StaticPage):
    def __init__(self, storage_manager):
        super().__init__(
            page_title="Campaigns",
            page_route="/campaigns",
            page_description="Campaigns",
            storage_manager=storage_manager,
        )
        self.tcn_adapter = tcn_adapter()
        self.report_df = pd.DataFrame()
        self.campaign_table_date = datetime.now().strftime("%Y-%m-%d")
        self.right_view_top = "view_cards"
        self.right_view_bottom = "none_selected"
        self.campaigns_df = None
        self._load_campaigns_data()

    def _load_campaigns_data(self):
        start_datetime, end_datetime = self.tcn_adapter.get_time_range(
            start_date=self.campaign_table_date,
            start_time="0800",
            end_date=self.campaign_table_date,
            end_time="2300",
            full_day=False,
        )
        self.campaigns_df = self.tcn_adapter.list_campaigns(
            start_datetime, end_datetime
        )

    def _render_campaign_table_date_picker(self):
        with ui.card().tight().classes(
            "flex flex-row items-center rounded-md px-1 py-0.5 pl-2 cursor-pointer"
        ).style("height:100%") as date_card:
            ui.label(self.campaign_table_date).classes("text-md font-semibold pt-1")
            ui.icon("calendar_today").classes("pl-1")

            menu = ui.menu().props("auto-close")
            menu.target = date_card  # Bind the menu to the card
            with menu:
                ui.date(
                    value=self.campaign_table_date,
                    on_change=self._handle_campaign_date_change,
                )

    def _handle_campaign_date_change(self, date):
        print(date)
        self.campaign_table_date = date.value
        self._load_campaigns_data()
        self._render_campaigns_table.refresh()
        self._render_layout.refresh()
        self._render_right_column.refresh()

    @ui.refreshable
    def _render_campaigns_table(self):
        if self.campaigns_df is None:
            with ui.card().classes(
                "w-full h-[25vh] border border-gray-200 rounded-xl justify-center items-center flex flex-col"
            ):
                ui.icon("o_calendar_month").classes("text-4xl")
                ui.label("No campaigns found for the selected date range.").classes(
                    "text-lg text-bold"
                )
            return

        # Add percentage complete column
        campaigns_df = self.campaigns_df.copy()
        campaigns_df["Percentage Complete"] = (
            campaigns_df["Completed Records"] / campaigns_df["Total Records"] * 100
        ).round(2).astype(str) + "%"

        # Get status code definitions
        status_code_definitions = self.tcn_adapter.get_status_code_definitions()

        # Add status code definition column
        campaigns_df["Status"] = campaigns_df["Status Code"].map(
            status_code_definitions
        )

        # Define indicator colors based on status codes
        def get_indicator_color(status_code):
            if status_code in [1510, 1500, 1410, 1400, 1310, 1300]:
                return "green"
            elif status_code in [1530, 1520, 1420, 1430, 1330, 1320]:
                return "orange"
            elif status_code in [1200]:
                return "blue"
            elif status_code in [1000, 1100, 1210, 1220]:
                return "yellow"
            else:
                return "gray"  # Default color for unspecified status codes

        # Add indicator column with color information
        campaigns_df["Indicator"] = campaigns_df["Status Code"].apply(
            get_indicator_color
        )

        # Define column definitions for AgGrid
        column_defs = [
            {
                "headerName": "",
                "field": "Indicator",
                "width": 30,
                "cellClassRules": {
                    "bg-green-500 text-green-500": 'x == "green"',
                    "bg-orange-500 text-orange-500": 'x == "orange"',
                    "bg-blue-500 text-blue-500": 'x == "blue"',
                    "bg-yellow-500 text-yellow-500": 'x == "yellow"',
                    "bg-gray-500 text-gray-500": 'x == "gray"',
                },
                "cellRenderer": """
                    class IndicatorRenderer {
                        init(params) {
                            this.eGui = document.createElement('div');
                            this.eGui.innerHTML = `<i class="material-icons">circle</i>`;
                            this.eGui.style.display = 'flex';
                            this.eGui.style.justifyContent = 'center';
                            this.eGui.style.alignItems = 'center';
                            this.eGui.style.height = '100%';
                        }
                        getGui() {
                            return this.eGui;
                        }
                    }
                """,
            },
            {"headerName": "Campaign", "field": "Broadcast ID"},
            {
                "headerName": "# Records",
                "field": "Total Records",
                "type": "numericColumn",
            },
            {
                "headerName": "# Completed",
                "field": "Completed Records",
                "type": "numericColumn",
            },
            {
                "headerName": "% Complete",
                "field": "Percentage Complete",
                "type": "numericColumn",
            },
        ]

        # Convert DataFrame to list of dictionaries for AgGrid
        row_data = campaigns_df.to_dict("records")

        # Create and return the AgGrid
        return (
            ui.aggrid(
                {
                    "columnDefs": column_defs,
                    "rowData": row_data,
                    "defaultColDef": {
                        "sortable": True,
                        "cellStyle": {
                            "text-align": "right",
                        },
                    },
                    "rowSelection": "single",  # Enable row selection
                    "suppressCellSelection": True,  # Disable cell selection
                    "suppressCellFocus": True,  # Remove cell highlighting
                    "rowStyle": {"cursor": "pointer"},  # Add pointer cursor to rows
                }
            )
            .classes(
                "w-full h-[25vh] border border-gray-200 rounded-xl overflow-hidden"
            )
            .on(
                "cellClicked",  # Change from cellClicked to rowClicked
                lambda e: self._render_campaign_details(e.args["data"]["Broadcast ID"]),
            )
        )

    def _render_campaign_details(self, campaign_id):
        report = self.tcn_adapter.get_report(campaign_id, return_unformatted=True)

        def replace_all(df, column_name, search_string, new_string):
            df[column_name] = df[column_name].apply(
                lambda x: new_string if x == search_string else x
            )
            return df

        def calculate_time_elapsed(df, column_name):
            def seconds_to_hhmmss(seconds):
                if pd.isna(seconds):
                    return ""
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours:02}:{minutes:02}:{secs:02}"

            df[column_name] = df[column_name].apply(seconds_to_hhmmss)

            return df

        def concat_columns(df, new_column_name, column_a, column_b):
            def safe_concat(x, y):
                if pd.isna(x) or pd.isna(y):
                    return ""
                return f"{x} - {y}"

            df[new_column_name] = df.apply(
                lambda row: safe_concat(row[column_a], row[column_b]), axis=1
            )
            return df

        def handle_blank_results(df):
            global error_df

            for index, row in df.iterrows():
                if pd.isna(row["Result"]):
                    interaction = row["Interaction"]
                    tcn_result = row["TCN Result"]
                    if interaction == "Answering Machine" or interaction == "No Answer":
                        df.at[index, "Result"] = interaction
                    elif "Link" in str(tcn_result) and "Ab" not in str(tcn_result):
                        if "error_df" not in globals():
                            error_df = pd.DataFrame(columns=df.columns)
                        error_df = pd.concat(
                            [error_df, pd.DataFrame([row])], ignore_index=True
                        )
                        df = df.drop(index)
            return df

        col_widths = [
            40,
            100,
            20,
            40,
            40,
            40,
            10,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            20,
            40,
            40,
            1000,
            10,
            10,
            10,
            10,
        ]
        df = pd.read_fwf(report, widths=col_widths)

        df = replace_all(df, "Agent ID", 2115221, "MPP")
        df = replace_all(df, "Agent ID", 2133845, "ARC")
        df = replace_all(df, "Agent ID", 2156762, "CMO")
        df = replace_all(df, "Agent ID", 2144867, "CJE")
        df = concat_columns(df, "Interaction Result", "Interaction", "Result")
        df = calculate_time_elapsed(df, "Call Duration")

        df = handle_blank_results(df)

        self.report_df = df
        self._render_report_visuals.refresh()

    @ui.refreshable
    def _render_report_visuals(self):
        if self.report_df.empty:
            with ui.card().classes(
                "w-full h-[55vh] justify-center items-center flex flex-col"
            ):
                ui.icon("o_analytics").classes("text-4xl text-gray-400")
                ui.label("Select a campaign to view analysis").classes(
                    "text-lg text-gray-500"
                )
        else:
            with ui.column().classes("w-full h-[55vh] gap-0"):
                with ui.scroll_area().style("width:100%;height:100%;"):
                    ComprehensiveCallAnalysis(self.report_df).render()

    def _render_left_column(self):
        with ui.column().classes("w-full h-full"):
            with ui.row().classes("w-full items-center"):
                with ui.card().tight().classes(
                    "flex flex-row flex-1 rounded-md py-2 pl-2 bg-transparent"
                ):
                    ui.label("Campaign Manager").classes("text-lg font-bold")
                self._render_campaign_table_date_picker()
            self._render_campaigns_table()
            self._render_report_visuals()

    def handle_on_grid_item_click(self, grid_item_path):
        self.right_view_top = grid_item_path
        self._render_right_column.refresh()

    @ui.refreshable
    def _render_right_column(self):
        grid_items = [
            {
                "grid_item_name": "Smart Scheduler",
                "grid_item_icon": "o_phone",
                "grid_item_path": "smart-scheduler",
                "grid_button_callback": lambda: self.handle_on_grid_item_click(
                    "view_smart_scheduler"
                ),
            },
        ]

        with ui.column().classes("w-full h-full gap-4"):
            # Top Card
            with ui.card().classes("w-full h-[20vh]"):
                if self.right_view_top == "view_cards":
                    for index, grid_item in enumerate(grid_items):
                        MiniGridCard(**grid_item, index=index).render()
                elif self.right_view_top == "view_smart_scheduler":
                    with ui.row().style("width:100%;"):
                        ui.button(icon="o_arrow_back").props("flat round").on(
                            "click",
                            lambda: self.handle_on_grid_item_click("view_cards"),
                        )

            # Bottom Card
            with ui.card().classes("w-full h-[65vh]"):
                if self.right_view_bottom == "none_selected":
                    with ui.row().classes("w-full h-full items-center justify-center"):
                        ui.label("Report Details").classes("text-lg text-gray-500")
                elif (
                    self.right_view_bottom == "show_details"
                    and not self.report_df.empty
                ):
                    with ui.scroll_area().classes("w-full h-full"):
                        # Select columns to display
                        columns_to_display = [
                            "Client Name",
                            "Call DateTime",
                            "Call Duration",
                            "Agent ID",
                            "Interaction",
                            "Result",
                            "Score",
                            "TCN Short",
                        ]

                        display_df = self.report_df[columns_to_display].copy()

                        # Create table
                        with ui.table().classes("w-full").props("dense bordered"):
                            with ui.table_head():
                                with ui.table_row():
                                    for col in columns_to_display:
                                        ui.table_cell(col)

                            with ui.table_body():
                                for _, row in display_df.iterrows():
                                    with ui.table_row():
                                        for col in columns_to_display:
                                            ui.table_cell(str(row[col]))

    @ui.refreshable
    def _render_layout(self):
        with ui.grid(columns=2).classes("w-full h-[85vh]"):
            self._render_left_column()
            self._render_right_column()

    def content(self):
        ui.add_head_html(
            """
        <style>
        .animate-card {
            animation: fadeInDrop 0.5s ease-out forwards;
        }

        @keyframes fadeInDrop {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
        """
        )
        self._render_layout()


def campaigns_page(storage_manager):
    page = CampaignsPage(storage_manager)
    page.render()
