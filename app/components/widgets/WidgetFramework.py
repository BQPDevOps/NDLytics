from abc import ABC
from middleware.dynamo import DynamoMiddleware
from middleware.s3 import S3Middleware
from datetime import datetime
import pandas as pd


class WidgetFramework(ABC):
    def __init__(self, widget_configuration: dict):
        self.widget_configuration = widget_configuration
        self.s3_client = S3Middleware()
        self.dynamo_client = DynamoMiddleware("NDL_Companies_Table")
        self.s3_bucket = "ndl-system-storage-v2"
        self.s3_master_key_map = {
            "accounts": "protected/datasets/by_portfolio/platform/accounts/ac_master.csv",
            "transactions": "protected/datasets/by_portfolio/platform/transactions/tr_master.csv",
            "contacts": "protected/datasets/by_portfolio/platform/contacts/co_master.csv",
            "outbound": "protected/datasets/by_portfolio/platform/outbound/od_master.csv",
        }
        self.required_datasets = self.widget_configuration["required_datasets"]
        self.company_id = self.widget_configuration["company_id"]
        self.widget_id = self.widget_configuration["widget_id"]
        self.data_store = {}
        self._pull_required_data()
        self.cached_metrics = self.check_cache()

    def _pull_metric_cache(self):
        key = {"company_id": {"S": self.company_id}}
        item = self.dynamo_client.get_item(key)

        def parse_dynamo_type(value):
            if isinstance(value, dict):
                if "M" in value:
                    return {k: parse_dynamo_type(v) for k, v in value["M"].items()}
                if "L" in value:
                    return [parse_dynamo_type(v) for v in value["L"]]
                for type_key in ["S", "N", "BOOL"]:
                    if type_key in value:
                        if type_key == "N":
                            try:
                                return int(value[type_key])
                            except ValueError:
                                return float(value[type_key])
                        return value[type_key]
            return value

        if item and "metric_cache" in item:
            return parse_dynamo_type(item["metric_cache"])
        return {}

    def is_widget_cached(self):
        cache = self._pull_metric_cache()
        if self.widget_id not in cache:
            key = {"company_id": {"S": self.company_id}}
            update_expression = "SET metric_cache.#wid = :empty"
            expression_values = {":empty": {"M": {}}}
            expression_names = {"#wid": self.widget_id}
            self.dynamo_client.update_item(
                key, update_expression, expression_values, expression_names
            )
            return {}
        return cache.get(self.widget_id, {})

    def is_cache_valid(self):
        metrics = self.is_widget_cached()
        if not metrics or "last_modified" not in metrics:
            return False
        last_modified = datetime.fromtimestamp(int(metrics["last_modified"])).date()
        return last_modified == datetime.now().date()

    def check_cache(self):
        metrics = self.is_widget_cached()
        if metrics and "last_modified" in metrics and self.is_cache_valid():
            return metrics
        return {}

    def update_metric_cache(self, metrics):
        """Update the metric cache in DynamoDB"""
        if not metrics:
            return

        key = {"widget_id": {"S": self.widget_id}, "company_id": {"S": self.company_id}}

        # Create update expression for flattened structure
        update_expression = "SET "
        expression_values = {}

        for k, v in metrics.items():
            update_expression += f"#{k} = :{k}, "
            expression_values[f":{k}"] = v

        # Remove trailing comma and space
        update_expression = update_expression.rstrip(", ")

        # Add expression attribute names
        expression_names = {f"#{k}": k for k in metrics.keys()}

        try:
            self.dynamo_client.update_item(
                key=key,
                update_expression=update_expression,
                expression_attribute_values=expression_values,
                expression_attribute_names=expression_names,
            )
        except Exception as e:
            print(f"Error updating metric cache: {str(e)}")
            raise

    def is_recalc_needed(self):
        return not bool(self.cached_metrics)

    def get_cached(self):
        return self.cached_metrics

    def set_cached(self, metrics: dict):
        self.cached_metrics = metrics

    def _pull_required_data(self):
        for dataset in self.required_datasets:
            self.data_store[dataset] = self.s3_client.read_csv_to_dataframe(
                bucket_name=self.s3_bucket, file_key=self.s3_master_key_map[dataset]
            )
        self._apply_datatype_formatting()

    def _process_accounts(self, dataframe):
        column_map = {
            "account_status": "string",
            "amount_paid": "float",
            "client_name": "string",
            "client_number": "string",
            "current_upb": "float",
            "file_number": "string",
            "listed_date": "date",
            "listed_date_day": "int",
            "listed_date_month": "int",
            "listed_date_year": "int",
            "operator": "string",
            "original_upb_loaded": "float",
            "tu_score": "int",
            "zip_code": "string",
        }
        column_keys = column_map.keys()
        for key in column_keys:
            if key in dataframe.columns:
                dataframe[key] = dataframe[key].apply(
                    lambda x: self._process_value(column_map[key], x)
                )
        return dataframe

    def _process_contacts(self, dataframe):
        column_map = {
            "account_balance": "float",
            "account_status": "string",
            "client_number": "string",
            "completed": "int",
            "created_date": "date",
            "created_date_day": "int",
            "created_date_month": "int",
            "created_date_year": "int",
            "done_by": "string",
            "due_date": "date",
            "due_date_day": "int",
            "due_date_month": "int",
            "due_date_year": "int",
            "file_number": "string",
            "operator": "string",
            "payment_amount": "float",
        }
        column_keys = column_map.keys()
        for key in column_keys:
            if key in dataframe.columns:
                dataframe[key] = dataframe[key].apply(
                    lambda x: self._process_value(column_map[key], x)
                )
        return dataframe

    def _process_transactions(self, dataframe):
        column_map = {
            "client_number": "string",
            "contingency_amount": "float",
            "description": "string",
            "file_number": "string",
            "operator": "stirng",
            "payment_amount": "float",
            "payment_date": "date",
            "payment_date_day": "int",
            "payment_date_month": "int",
            "payment_date_year": "int",
            "posted_by": "string",
            "posted_date": "date",
            "posted_date_day": "int",
            "posted_date_month": "int",
            "posted_date_year": "int",
            "transaction_type": "string",
        }
        column_keys = column_map.keys()
        for key in column_keys:
            if key in dataframe.columns:
                dataframe[key] = dataframe[key].apply(
                    lambda x: self._process_value(column_map[key], x)
                )
        return dataframe

    def _process_outbound(self, dataframe):
        column_map = {
            "broadcast_id": "string",
            "agent_id": "string",
            "caller_id": "string",
            "call_id": "string",
            "call_recorded": "boolean",
            "short_code": "string",
            "call_type": "string",
            "delivery_cost": "float",
            "delivery_length": "int",
            "file_number": "string",
            "client_number": "string",
            "score": "int",
            "status": "string",
            "zip_code": "string",
            "balance": "float",
            "phone_cell": "string",
            "phone_home": "string",
            "phone_work": "string",
            "phone_other": "string",
            "tcn_dialed": "string",
            "start_time": "datetime",
            "interaction": "string",
            "result": "string",
            "call_completed_date_day": "int",
            "call_completed_date_month": "int",
            "call_completed_date_year": "int",
            "call_completed_date_hour": "int",
            "call_completed_date_minute": "int",
            "charge_date_month": "int",
            "charge_date_day": "int",
            "charge_date_year": "int",
        }
        column_keys = column_map.keys()
        for key in column_keys:
            if key in dataframe.columns:
                dataframe[key] = dataframe[key].apply(
                    lambda x: self._process_value(column_map[key], x)
                )
        return dataframe

    def _apply_datatype_formatting(self):
        for dataset in self.required_datasets:
            if dataset == "accounts":
                self.data_store[dataset] = self._process_accounts(
                    self.data_store[dataset]
                )
            elif dataset == "transactions":
                self.data_store[dataset] = self._process_transactions(
                    self.data_store[dataset]
                )
            elif dataset == "contacts":
                self.data_store[dataset] = self._process_contacts(
                    self.data_store[dataset]
                )

    def get_accounts(self):
        if "accounts" not in self.data_store:
            self._pull_required_data()
        return self.data_store.get("accounts", pd.DataFrame())

    def get_transactions(self):
        if "transactions" not in self.data_store:
            self._pull_required_data()
        return self.data_store.get("transactions", pd.DataFrame())

    def get_contacts(self):
        if "contacts" not in self.data_store:
            self._pull_required_data()
        return self.data_store.get("contacts", pd.DataFrame())

    def get_outbound(self):
        if "outbound" not in self.data_store:
            self._pull_required_data()
        return self.data_store.get("outbound", pd.DataFrame())

    def _process_value(self, type_name: str, value):
        """Process a value based on its type name."""
        if pd.isna(value):
            return None

        if type_name == "string":
            return str(value)
        elif type_name == "float":
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        elif type_name == "int":
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        elif type_name == "date":
            try:
                return pd.to_datetime(value, format="%Y-%m-%d")
            except (ValueError, TypeError):
                return None
        elif type_name == "bool":
            return bool(value)
        return value
