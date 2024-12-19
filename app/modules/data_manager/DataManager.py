import pandas as pd
from io import StringIO
from botocore.exceptions import ClientError
from datetime import datetime
from decimal import Decimal

from config import config
from middleware.s3 import S3Middleware


class DataManager:
    def __init__(self):
        self.s3_middleware = S3Middleware()
        self.s3_bucket = config.aws_s3_system_bucket
        self.file_map = {
            "transactions": "protected/datasets/by_portfolio/platform/transactions/tr_master.csv",
            "contacts": "protected/datasets/by_portfolio/platform/contacts/co_master.csv",
            "accounts": "protected/datasets/by_portfolio/platform/accounts/ac_master.csv",
            "outbound": "protected/datasets/by_portfolio/platform/outbound/od_master.csv",
            "preprocess": "protected/datasets/by_portfolio/platform/preprocessed_key_values.csv",
        }
        self.state = {}
        self.required_keys = []

    def _read_csv(self, bucket_name, file_key):
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)

            # Read the CSV content into a pandas DataFrame
            csv_content = response["Body"].read().decode("utf-8")
            dataframe = pd.read_csv(StringIO(csv_content))
            return dataframe
        except ClientError as e:
            # Logging the error
            print(f"Error reading CSV file: {e}")
            return None

    def _load_or_calculate_data(self, force_refresh=False):
        try:
            if not force_refresh:
                response = self.s3.read_csv_to_dataframe(
                    bucket_name=self.s3_bucket, file_key=self.calc_key
                )
                if (
                    response is not None
                    and not response.empty
                    and self._validate_cache(response)
                ):
                    self.cached_data = self._process_cached_data(response)
                    return
            self.cached_data = self._calculate_and_cache_data()
        except Exception as e:
            print(f"Cache loading error: {str(e)}")
            self.cached_data = self._calculate_and_cache_data()

    def _save_cached_data(self, data):
        """Save calculated data to S3"""
        try:
            df = pd.DataFrame([data])
            directory_path = "protected/datasets/by_portfolio/platform"
            file_name = "preprocessed_key_values.csv"

            success = self.s3.save_dataframe_to_csv(
                dataframe=df,
                bucket_name=self.s3_bucket,
                directory_path=directory_path,
                file_name=file_name,
            )

            if success:
                print("Successfully saved cache to S3")
            else:
                print("Failed to save cache to S3")
        except Exception as e:
            print(f"Error saving cache: {str(e)}")

    def _load_cached_data(self):
        """Load cached calculations from S3"""
        try:
            df = self.s3.read_csv_to_dataframe(
                bucket_name=self.s3_bucket, file_key=self.calc_key
            )
            return df
        except Exception as e:
            print(f"Error loading cached data: {str(e)}")
            return None

    def _validate_cache(self, df):
        if df.empty:
            return False
        today = datetime.now().strftime("%Y-%m-%d")
        has_required_keys = all(key in df.columns for key in self.required_keys)
        is_current = df["last_modified"].iloc[0] == today
        return has_required_keys and is_current

    def _process_value(self, type, value):
        if type == "string":
            return value
        elif type == "float":
            return Decimal(value).quantize(Decimal("0.01"))
        elif type == "date":
            return value.strftime("%Y-%m-%d")
        elif type == "int":
            return int(value)

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
