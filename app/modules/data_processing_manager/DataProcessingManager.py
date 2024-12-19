import pandas as pd
import numpy as np
from middleware.s3 import create_s3_middleware


class DataProcessingManager:
    def __init__(self):
        self.s3 = create_s3_middleware()
        self.s3_bucket = "nda-storage-v1"
        self.data_types = {
            "transactions": "protectect/datasets/by_portfolio/platform/transactions/tr_master.csv",
            "calls": "protectect/datasets/by_portfolio/platform/calls/od_master.csv",
            "accounts": "protectect/datasets/by_portfolio/platform/accounts/ac_master.csv",
            "contacts": "protectect/datasets/by_portfolio/platform/contacts/co_master.csv",
        }
        self.data_store = {}

    def _float64_to_int(self, dataframe, columns):
        for column in columns:
            dataframe[column] = dataframe[column].fillna(0)
            dataframe[column] = dataframe[column].astype(np.int64)
        return dataframe

    def _float64_to_str(self, dataframe, columns, fill_value=0):
        for column in columns:
            dataframe[column] = dataframe[column].fillna(fill_value)
            dataframe[column] = dataframe[column].astype(str)
        return dataframe

    def _object_to_int64(self, dataframe, columns):
        for column in columns:
            dataframe[column] = dataframe[column].fillna(-1)
            dataframe[column] = (
                pd.to_numeric(dataframe[column], errors="coerce")
                .fillna(-1)
                .astype("int64")
            )
        return dataframe

    def _process_transactions(self, dataframe):
        dataframe = self._float64_to_int(
            dataframe, ["posted_date_month", "posted_date_year", "posted_date_day"]
        )
        self.data_store["transactions"] = dataframe

    def _process_calls(self, dataframe):
        dataframe = self._object_to_int64(dataframe, ["agent_id"])
        dataframe = self._float64_to_str(
            dataframe,
            ["phone_cell", "phone_home", "phone_work", "phone_other", "tcn_dialed"],
            "000-000-0000",
        )
        self.data_store["calls"] = dataframe

    def _process_accounts(self, dataframe):
        dataframe = self._float64_to_str(dataframe, ["zip"])
        self.data_store["accounts"] = dataframe

    def _process_contacts(self, dataframe):
        dataframe = self._float64_to_int(
            dataframe,
            [
                "due_date_year",
                "due_date_month",
                "due_date_day",
                "created_date_year",
                "created_date_month",
                "created_date_day",
                "completed",
            ],
        )
        self.data_store["contacts"] = dataframe

    def _get_dataframe(self, file_key):
        """Retrieve a DataFrame from the store or load it from S3"""
        if file_key not in self.data_store:
            data = self.s3.read_csv_to_dataframe(
                bucket_name=self.s3_bucket, file_key=file_key
            )

            self.data_store[file_key] = data

            if file_key == self.data_types["transactions"]:
                self._process_transactions(data)
            elif file_key == self.data_types["calls"]:
                self._process_calls(data)
            elif file_key == self.data_types["accounts"]:
                self._process_accounts(data)
            elif file_key == self.data_types["contacts"]:
                self._process_contacts(data)

        return self.data_store[file_key]

    def load_data(self, data_type):
        if data_type not in self.data_types:
            raise ValueError(f"Invalid data type: {data_type}")
        file_key = self.data_types[data_type]
        self.data_store[data_type] = self._get_dataframe(file_key)
