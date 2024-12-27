import boto3
import pandas as pd
from io import StringIO
from datetime import datetime


class DataProcessor:
    def __init__(self, bucket_name, region_name="us-east-1"):
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.bucket = bucket_name
        self.data_store = {}
        self.file_mapping = {
            "accounts": "protected/datasets/by_portfolio/platform/accounts/ac_master.csv",
            "transactions": "protected/datasets/by_portfolio/platform/transactions/tr_master.csv",
            "contacts": "protected/datasets/by_portfolio/platform/contacts/co_master.csv",
            "outbound": "protected/datasets/by_portfolio/platform/outbound/od_master.csv",
        }

        self.dtypes = {
            "accounts": {
                "account_status": str,
                "client_name": str,
                "client_number": str,
                "file_number": str,
                "operator": str,
                "zip_code": str,
                "listed_date_day": int,
                "listed_date_month": int,
                "listed_date_year": int,
                "tu_score": int,
                "amount_paid": float,
                "current_upb": float,
                "original_upb_loaded": float,
            },
            "contacts": {
                "account_status": str,
                "client_number": str,
                "done_by": str,
                "file_number": str,
                "operator": str,
                "completed": int,
                "created_date_day": int,
                "created_date_month": int,
                "created_date_year": int,
                "due_date_day": int,
                "due_date_month": int,
                "due_date_year": int,
                "account_balance": float,
                "payment_amount": float,
            },
            "transactions": {
                "client_number": str,
                "description": str,
                "file_number": str,
                "operator": str,
                "posted_by": str,
                "transaction_type": str,
                "payment_date_day": int,
                "payment_date_month": int,
                "payment_date_year": int,
                "posted_date_day": int,
                "posted_date_month": int,
                "posted_date_year": int,
                "contingency_amount": float,
                "payment_amount": float,
            },
            "outbound": {
                "broadcast_id": str,
                "agent_id": str,
                "caller_id": str,
                "call_id": str,
                "short_code": str,
                "call_type": str,
                "file_number": str,
                "client_number": str,
                "status": str,
                "zip_code": str,
                "phone_cell": str,
                "phone_home": str,
                "phone_work": str,
                "phone_other": str,
                "tcn_dialed": str,
                "interaction": str,
                "result": str,
                "call_recorded": bool,
                "delivery_length": int,
                "score": int,
                "call_completed_date_day": int,
                "call_completed_date_month": int,
                "call_completed_date_year": int,
                "call_completed_date_hour": int,
                "call_completed_date_minute": int,
                "charge_date_month": int,
                "charge_date_day": int,
                "charge_date_year": int,
                "delivery_cost": float,
                "balance": float,
            },
        }

    def get_dataframe(self, short_name):
        if short_name not in self.file_mapping:
            raise ValueError(f"Unknown file reference: {short_name}")

        s3_key = self.file_mapping[short_name]

        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            csv_content = response["Body"].read().decode("utf-8")

            # Create dtype dictionary - handle all numeric columns as float initially
            dtype_dict = {}
            for col, dtype in self.dtypes[short_name].items():
                if dtype == int or dtype == float:
                    dtype_dict[col] = (
                        str  # Change to string to prevent pandas auto-conversion
                    )
                elif dtype == str:
                    dtype_dict[col] = str
                else:
                    dtype_dict[col] = object

            print(f"Loading {short_name} with dtypes:", dtype_dict)
            df = pd.read_csv(StringIO(csv_content), low_memory=False)

            return self._format_dataframe(short_name, df)
        except Exception as e:
            raise Exception(f"Error loading {short_name}: {str(e)}")

    def _format_dataframe(self, short_name, df):
        if short_name == "accounts":
            string_columns = ["client_number", "file_number"]
            float_columns = ["amount_paid", "current_upb", "original_upb_loaded"]
            int_columns = [
                "listed_date_day",
                "listed_date_month",
                "listed_date_year",
                "tu_score",
            ]
            # Process in order: floats, integers, strings
            for col in float_columns:
                df[col] = df[col].apply(self._sanitize_float_numbers)
            for col in int_columns:
                df[col] = df[col].apply(self._sanitize_integers)
            df = self._sanitize_string_columns(df, string_columns)
            # Create date after sanitizing components
            df["listed_date"] = pd.to_datetime(
                {
                    "year": df["listed_date_year"],
                    "month": df["listed_date_month"],
                    "day": df["listed_date_day"],
                },
                errors="coerce",
            )

        elif short_name == "contacts":
            string_columns = ["client_number", "file_number"]
            float_columns = ["account_balance", "payment_amount"]
            int_columns = [
                "completed",
                "created_date_day",
                "created_date_month",
                "created_date_year",
                "due_date_day",
                "due_date_month",
                "due_date_year",
            ]
            # Process in order: floats, integers, strings
            for col in float_columns:
                df[col] = df[col].apply(self._sanitize_float_numbers)
            for col in int_columns:
                df[col] = df[col].apply(self._sanitize_integers)
            df = self._sanitize_string_columns(df, string_columns)
            # Create dates after sanitizing components
            df["created_date"] = pd.to_datetime(
                {
                    "year": df["created_date_year"],
                    "month": df["created_date_month"],
                    "day": df["created_date_day"],
                },
                errors="coerce",
            )
            df["due_date"] = pd.to_datetime(
                {
                    "year": df["due_date_year"],
                    "month": df["due_date_month"],
                    "day": df["due_date_day"],
                },
                errors="coerce",
            )

        elif short_name == "transactions":
            string_columns = ["client_number", "file_number"]
            float_columns = ["contingency_amount", "payment_amount"]
            int_columns = [
                "payment_date_day",
                "payment_date_month",
                "payment_date_year",
                "posted_date_day",
                "posted_date_month",
                "posted_date_year",
            ]
            # Process in order: floats, integers, strings
            for col in float_columns:
                df[col] = df[col].apply(self._sanitize_float_numbers)
            for col in int_columns:
                df[col] = df[col].apply(self._sanitize_integers)
            df = self._sanitize_string_columns(df, string_columns)
            # Create dates after sanitizing components
            df["payment_date"] = pd.to_datetime(
                {
                    "year": df["payment_date_year"],
                    "month": df["payment_date_month"],
                    "day": df["payment_date_day"],
                },
                errors="coerce",
            )
            df["posted_date"] = pd.to_datetime(
                {
                    "year": df["posted_date_year"],
                    "month": df["posted_date_month"],
                    "day": df["posted_date_day"],
                },
                errors="coerce",
            )

        elif short_name == "outbound":
            string_columns = [
                "client_number",
                "file_number",
                "broadcast_id",
                "agent_id",
                "caller_id",
                "call_id",
                "short_code",
                "call_type",
                "status",
                "zip_code",
                "phone_cell",
                "phone_home",
                "phone_work",
                "phone_other",
                "tcn_dialed",
                "interaction",
                "result",
            ]
            float_columns = ["delivery_cost", "balance"]
            int_columns = [
                "delivery_length",
                "score",
                "call_completed_date_day",
                "call_completed_date_month",
                "call_completed_date_year",
                "call_completed_date_hour",
                "call_completed_date_minute",
                "charge_date_month",
                "charge_date_day",
                "charge_date_year",
            ]

            # Process in order: floats, integers, strings
            for col in float_columns:
                if col in df.columns:
                    # Convert NONE to 0 before sanitization
                    df[col] = df[col].apply(
                        lambda x: 0 if str(x).strip().upper() == "NONE" else x
                    )
                    df[col] = df[col].apply(self._sanitize_float_numbers)
            for col in int_columns:
                if col in df.columns:
                    df[col] = df[col].apply(self._sanitize_integers)
            df = self._sanitize_string_columns(
                df, [col for col in string_columns if col in df.columns]
            )

        return df

    def _safe_date_convert(self, row, date_column_prefix):
        """Convert separate date columns into a datetime object"""
        try:
            year = row.get(f"{date_column_prefix}_date_year", None)
            month = row.get(f"{date_column_prefix}_date_month", None)
            day = row.get(f"{date_column_prefix}_date_day", None)

            # Handle NaN, None, and zero values
            if pd.isna(year) or pd.isna(month) or pd.isna(day):
                return pd.NaT

            # Convert to integer safely
            try:
                year = int(float(year))
                month = int(float(month))
                day = int(float(day))
            except:
                return pd.NaT

            # Handle zero dates or invalid dates
            if year == 0 or month == 0 or day == 0 or month > 12 or day > 31:
                return pd.NaT

            # Handle 2-digit years
            if year < 100:
                year = 2000 + year

            try:
                return pd.Timestamp(year=year, month=month, day=day)
            except:
                return pd.NaT

        except Exception as e:
            return pd.NaT

    def _sanitize_float_numbers(self, amount):
        """Clean and convert float numbers to float with 2 decimal places"""
        try:
            # First check for NONE or NULL values
            if pd.isna(amount) or amount is None:
                return 0.00

            # Clean the string value
            amount_str = str(amount).strip().upper()
            if amount_str in ["NONE", "", "NULL"]:
                return 0.00

            # Remove quotes, currency symbols, and other special chars
            amount_str = (
                str(amount)
                .strip()
                .replace('"', "")
                .replace("'", "")
                .replace("$", "")
                .replace(",", "")
            )
            # Keep only digits, decimal point and negative sign
            amount_str = "".join(c for c in amount_str if c.isdigit() or c in ".-")
            if not amount_str:  # If string is empty after cleaning
                return 0.00

            is_negative = amount_str.startswith("-")
            parts = amount_str.replace("-", "").split(".")
            amount_str = parts[0] + ("." + parts[1] if len(parts) > 1 else "")
            value = float(amount_str) if amount_str else 0.00
            return round((-value if is_negative else value), 2)
        except Exception as e:
            print(
                f"Error sanitizing float: Input value '{amount}' of type {type(amount)}"
            )
            print(f"Error details: {str(e)}")
            return 0.00

    def _sanitize_integers(self, value):
        """Convert values to clean integers"""
        try:
            if pd.isna(value) or value is None:
                return 0
            if isinstance(value, (int, float)):
                return int(value)
            return 0
        except Exception as e:
            return 0

    def _sanitize_string_columns(self, df, columns):
        """Convert only numeric-intended string columns with 'S' prefix, leave regular strings as is"""
        numeric_string_columns = [
            "client_number",
            "file_number",
        ]  # Columns that should be treated as numeric strings

        for col in columns:
            if col in numeric_string_columns:
                df[col] = df[col].apply(
                    lambda x: (
                        f"S{str(int(float(x)))}"
                        if pd.notna(x) and str(x).strip() != ""
                        else ""
                    )
                )
            else:
                df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else "")
        return df

    def get_accounts(self, force=False):
        """Load accounts DataFrame with caching logic"""
        if "accounts" in self.data_store and not force:
            return self.data_store["accounts"]

        df = self.get_dataframe("accounts")
        self.data_store["accounts"] = df
        return df

    def get_contacts(self, force=False):
        """Load contacts DataFrame with caching logic"""
        if "contacts" in self.data_store and not force:
            return self.data_store["contacts"]

        df = self.get_dataframe("contacts")
        self.data_store["contacts"] = df
        return df

    def get_transactions(self, force=False):
        """Load transactions DataFrame with caching logic"""
        if "transactions" in self.data_store and not force:
            return self.data_store["transactions"]

        df = self.get_dataframe("transactions")
        self.data_store["transactions"] = df
        return df

    def get_outbound(self, force=False):
        """Load outbound DataFrame with caching logic"""
        if "outbound" in self.data_store and not force:
            return self.data_store["outbound"]

        df = self.get_dataframe("outbound")
        self.data_store["outbound"] = df
        return df

    def get_grouped(
        self,
        short_name,
        group_column,
        group_value=None,
        sub_group_column=None,
        sub_group_value=None,
    ):
        """Get grouped data based on specified parameters"""
        data_methods = {
            "accounts": self.get_accounts,
            "transactions": self.get_transactions,
            "contacts": self.get_contacts,
            "outbound": self.get_outbound,
        }

        df = data_methods[short_name]()
        result = {}

        if group_column not in df.columns:
            raise ValueError(f"Group column '{group_column}' not found")
        if sub_group_column and sub_group_column not in df.columns:
            raise ValueError(f"Sub-group column '{sub_group_column}' not found")

        primary_groups = (
            [group_value] if group_value is not None else df[group_column].unique()
        )

        for primary_key in primary_groups:
            primary_df = df[df[group_column] == primary_key]

            if sub_group_column:
                sub_groups = (
                    [sub_group_value]
                    if sub_group_value
                    else primary_df[sub_group_column].unique()
                )

                for sub_key in sub_groups:
                    sub_df = primary_df[primary_df[sub_group_column] == sub_key]
                    result[str(sub_key)] = sub_df.to_dict("records")
            else:
                result[str(primary_key)] = primary_df.to_dict("records")

        return result

    def get_sum(self, short_name, columns):
        """Return sum of specified columns"""
        df = self.get_dataframe(short_name)
        return df[columns].sum()

    def get_average(self, short_name, columns):
        """Return average of specified columns"""
        df = self.get_dataframe(short_name)
        return df[columns].mean()

    def get_median(self, short_name, columns):
        """Return median of specified columns"""
        df = self.get_dataframe(short_name)
        return df[columns].median()

    def get_range(self, short_name, columns):
        """Return tuple of (max, min) for specified columns"""
        df = self.get_dataframe(short_name)
        return (df[columns].max(), df[columns].min())

    def get_unique_values(self, short_name, columns, include_count=False):
        """Return unique values for specified columns"""
        df = self.get_dataframe(short_name)

        if include_count:
            return {col: df[col].value_counts().to_dict() for col in columns}

        return {col: df[col].unique().tolist() for col in columns}
