from nicegui import ui
import pandas as pd
from datetime import datetime
from .WidgetFramework import WidgetFramework
from utils.func.create_date import create_date


class MTDMetricsWidget(WidgetFramework):
    def __init__(self, widget_configuration: dict):
        super().__init__(widget_configuration)
        self.force_refresh = widget_configuration.get("force_refresh", False)

        # Verify data loaded from parent
        for dataset in self.required_datasets:
            df = self.data_store.get(dataset)

        if self.is_recalc_needed() or self.force_refresh:
            self._calculate_metrics()

    def _safe_date_convert(self, row, prefix):
        """Safely convert date components to a datetime"""
        try:
            month = row[f"{prefix}_month"]
            day = row[f"{prefix}_day"]
            year = row[f"{prefix}_year"]

            if pd.isna(month) or pd.isna(day) or pd.isna(year):
                return pd.NaT

            # Convert float values to integers
            month = int(float(month))
            day = int(float(day))
            year = int(float(year))

            # Validate date components
            if month < 1 or month > 12 or day < 1 or day > 31 or year < 1900:
                return pd.NaT

            # Create date string directly
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            return pd.to_datetime(date_str)

        except Exception as e:
            return pd.NaT

    def _calculate_metrics(self):
        """Calculate all metrics and cache them"""
        metrics = {}

        # Calculate MTD metrics
        mtd_metrics = self._calculate_mtd_metrics()
        metrics["mtd_metrics"] = mtd_metrics

        # Add timestamp
        metrics["last_modified"] = int(datetime.now().timestamp())

        # Update cache
        self.update_metric_cache(metrics)

    def _calculate_mtd_metrics(self):
        """Calculate Month-to-Date metrics including collections and projections"""
        current_date = pd.Timestamp.now()
        current_month = current_date.replace(day=1)

        # Get transactions data
        transactions_df = self.get_transactions()

        # Convert date columns using create_date
        transactions_df["posted_date"] = transactions_df.apply(
            lambda x: self._safe_date_convert(x, "posted_date"), axis=1
        )
        transactions_df["payment_date"] = transactions_df.apply(
            lambda x: self._safe_date_convert(x, "payment_date"), axis=1
        )

        if not transactions_df.empty:
            # Calculate MTD collected
            mtd_filter = (transactions_df["posted_date"] >= current_month) & (
                transactions_df["posted_date"].notna()
            )
            mtd_collected = transactions_df[mtd_filter]["payment_amount"].sum()

            # Calculate projected futures
            futures_filter = (
                (transactions_df["payment_date"] > current_date)
                & (
                    transactions_df["payment_date"]
                    <= current_date + pd.offsets.MonthEnd(0)
                )
                & (transactions_df["posted_date"].isna())
            )
            projected_futures = transactions_df[futures_filter]["payment_amount"].sum()

        # Calculate total
        projected_total = mtd_collected + projected_futures

        return {
            "collected_mtd": round(mtd_collected, 2),
            "projected_futures": round(projected_futures, 2),
            "projected_total": round(projected_total, 2),
        }

    def render(self):
        """Render the metrics dashboard"""
        metrics = self.get_cached()

        with ui.card().classes("w-full p-6"):
            ui.label("MTD Collections").classes("text-2xl font-bold mb-4")

            if "mtd_metrics" in metrics:
                mtd = metrics["mtd_metrics"]
                with ui.grid(columns=2).classes("w-full gap-6 mt-6"):
                    # Collections Card
                    with ui.card().classes("p-4"):
                        ui.label("Current Month Collections").classes(
                            "text-lg font-bold mb-2"
                        )
                        with ui.column().classes("gap-2"):
                            ui.label(f"Collected MTD: ${mtd['collected_mtd']:,.2f}")
                            ui.label(
                                f"Projected Futures: ${mtd['projected_futures']:,.2f}"
                            )
                            ui.label(f"Projected Total: ${mtd['projected_total']:,.2f}")

                    # Projections by Status Card
                    with ui.card().classes("p-4"):
                        ui.label("Projections by Status").classes(
                            "text-lg font-bold mb-2"
                        )
                        with ui.column().classes("gap-2"):
                            ui.label(f"PACH: ${mtd['projected_pach']:,.2f}")
                            ui.label(f"PCRD: ${mtd['projected_pcrd']:,.2f}")
                            ui.label(f"PRA: ${mtd['projected_pra']:,.2f}")


def create_mtd_metrics_widget(widget_configuration: dict = None, force_refresh=False):
    """Factory function to create a new MTDMetricsWidget instance."""
    if widget_configuration is None:
        widget_configuration = {
            "required_datasets": ["transactions", "contacts"],
            "company_id": "ALL",
            "widget_id": "wgt_mtd_metrics",
            "force_refresh": force_refresh,
        }
    return MTDMetricsWidget(widget_configuration)
