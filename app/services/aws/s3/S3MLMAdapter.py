import boto3
import joblib
from io import BytesIO
from botocore.exceptions import NoCredentialsError, ClientError


class S3MLMAdapter:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name

    def save_model(self, key, model, performance_metrics):
        """
        Saves a machine learning model to S3.

        Args:
            key: The S3 key (path) for the model file.
            model: The machine learning model to save.
        """
        try:
            trained_model = {"model": model, **performance_metrics}
            model_bytes = BytesIO()
            joblib.dump(trained_model, model_bytes)
            model_bytes.seek(0)
            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=key, Body=model_bytes.getvalue()
            )
            print(f"Successfully saved model to s3://{self.bucket_name}/{key}")
        except NoCredentialsError:
            print("No AWS credentials found.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                print(f"The bucket {self.bucket_name} does not exist.")
            elif e.response["Error"]["Code"] == "AccessDenied":
                print("Access denied. Check your AWS permissions.")
            else:
                print(f"Error saving model to S3: {e}")

    def load_model(self, key):
        """
        Loads a machine learning model from S3.

        Args:
            key: The S3 key (path) for the model file.

        Returns:
            The loaded machine learning model, or None if an error occurred.
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            model_bytes = BytesIO(response["Body"].read())
            model_obj = joblib.load(model_bytes)
            model = model_obj["model"]
            performance_metrics = {
                "accuracy": model_obj.get("accuracy"),
                "precision": model_obj.get("precision"),
                "recall": model_obj.get("recall"),
                "f1": model_obj.get("f1"),
                "roc_auc": model_obj.get("roc_auc"),
                "confusion_matrix": model_obj.get("confusion_matrix"),
                "classification_report": model_obj.get("classification_report"),
            }
            print(f"Successfully loaded model from s3://{self.bucket_name}/{key}")
            return model, performance_metrics
        except NoCredentialsError:
            print("No AWS credentials found.")
        except ClientError as e:
            print(f"Error loading model from S3: {e}")
        return None

    async def model_exists(self, key):
        """
        Checks if a model exists in S3.

        Args:
            key: The S3 key (path) for the model file.

        Returns:
            True if the model exists, False otherwise.
        """
        try:
            await self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            print(f"Error checking if model exists in S3: {e}")
        return False
