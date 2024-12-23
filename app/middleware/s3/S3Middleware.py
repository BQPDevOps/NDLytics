import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import pandas as pd
from io import StringIO
import base64


class S3Middleware:
    def __init__(self, company_id=None, user_uuid=None):
        self.s3_client = boto3.client("s3")
        self.company_id = company_id
        self.user_uuid = user_uuid

    def get_file_content(self, bucket_name, file_key):
        """
        Get the content of a file from S3
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            return response["Body"].read()
        except ClientError as e:
            print(f"Error getting file content: {e}")
            return None

    def get_object(self, bucket_name, key):
        """
        Get an object from the specified S3 bucket.
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            return response
        except Exception as e:
            print(f"Error fetching object {key} from bucket {bucket_name}: {e}")
            return None

    def generate_presigned_url(self, bucket_name, file_key, expiration=3600):
        """
        Generate a presigned URL to share an S3 object
        """
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": file_key},
                ExpiresIn=expiration,
            )
            return response
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def list_objects(self, bucket_name, current_path):
        """
        Lists the objects in the current path.
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=current_path, Delimiter="/"
            )
            if "CommonPrefixes" in response:
                directories = [
                    prefix["Prefix"] for prefix in response["CommonPrefixes"]
                ]
            else:
                directories = []

            if "Contents" in response:
                files = [
                    content["Key"]
                    for content in response["Contents"]
                    if content["Key"] != current_path
                ]
            else:
                files = []

            return {"directories": directories, "files": files}
        except (NoCredentialsError, ClientError) as e:
            print(f"Error: {e}")
            return None

    def get_file_metadata(self, bucket_name, file_key):
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=file_key)
            return {
                "Size": response["ContentLength"],
                "LastModified": response["LastModified"].strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as e:
            print(f"Error fetching metadata for {file_key}: {e}")
            return {"Size": "Unknown", "LastModified": "Unknown"}

    def list_files(self, bucket_name, file_key, clean_prefixes=True):
        try:
            # List objects in the folder
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=file_key
            )
            if "Contents" in response:
                files = [content["Key"] for content in response["Contents"]]
                if clean_prefixes:
                    # Remove the prefix and return only file names
                    return [
                        file.replace(file_key, "") for file in files if file != file_key
                    ]
                else:
                    # Return full paths
                    return files
            else:
                return []
        except ClientError as e:
            # Logging the error
            print(f"Error listing files: {e}")
            return []

    def upload_file(self, bucket_name, file_key):
        try:
            # Upload file to S3
            self.s3_client.upload_file(file_key, bucket_name, file_key)
            return True
        except ClientError as e:
            # Logging the error
            print(f"Error uploading file: {e}")
            return False

    def read_csv_to_dataframe(self, bucket_name, file_key):
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)

            # Read the CSV content into a pandas DataFrame
            csv_content = response["Body"].read().decode("utf-8")
            dataframe = pd.read_csv(StringIO(csv_content), low_memory=False)
            return dataframe
        except ClientError as e:
            # Logging the error
            print(f"Error reading CSV file: {e}")
            return None

    def get_recent_uploads(self, bucket_name, limit=20):
        """
        Retrieves the keys of the most recently uploaded documents across all companies.

        :param bucket_name: Name of the S3 bucket
        :param limit: Number of recent documents to retrieve (default: 20)
        :return: List of tuples containing (key, last_modified) for the most recent uploads
        """
        try:
            # List all objects in the bucket
            paginator = self.s3_client.get_paginator("list_objects_v2")
            all_objects = []

            for page in paginator.paginate(Bucket=bucket_name):
                if "Contents" in page:
                    all_objects.extend(page["Contents"])

            # Filter objects that match the pattern 'company/protected/'
            filtered_objects = [
                obj for obj in all_objects if "/protected/" in obj["Key"]
            ]

            # Sort the filtered objects by last modified date (most recent first)
            sorted_objects = sorted(
                filtered_objects, key=lambda x: x["LastModified"], reverse=True
            )

            # Return the keys and last modified dates of the most recent uploads
            recent_uploads = [
                (obj["Key"], obj["LastModified"]) for obj in sorted_objects[:limit]
            ]

            return recent_uploads

        except ClientError as e:
            print(f"Error retrieving recent uploads: {e}")
            return []

    def save_dataframe_to_csv(self, dataframe, bucket_name, directory_path, file_name):
        """
        Saves a pandas DataFrame as a CSV file to S3.

        :param dataframe: pandas DataFrame to be saved
        :param bucket_name: Name of the S3 bucket
        :param directory_path: Path within the bucket where the file should be saved
        :param file_name: Name of the file to be saved (including .csv extension)
        :return: True if successful, False otherwise
        """
        try:
            # Create a buffer to hold the CSV data
            csv_buffer = StringIO()

            # Write the DataFrame to the buffer as CSV
            dataframe.to_csv(csv_buffer, index=False)

            # Move the buffer's pointer to the beginning
            csv_buffer.seek(0)

            key = f"{directory_path.strip('/')}/{file_name}"

            # Upload the file to S3
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=csv_buffer.getvalue(),
                ContentType="text/csv",
            )

            print(f"Successfully saved {file_name} to S3 bucket {bucket_name}")
            return True

        except Exception as e:
            print(f"Error saving DataFrame to CSV in S3: {e}")
            return False

    def get_file_content_base64(self, bucket_name, file_key):
        """
        Get the content of a file from S3 as base64 encoded string
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=file_key)
            file_content = response["Body"].read()
            return base64.b64encode(file_content).decode("utf-8")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            print(f"Error getting file content: {error_code} - {error_message}")
            return None
        except Exception as e:
            print(f"Unexpected error getting file content: {str(e)}")
            return None

    def put_object(self, bucket_name, key, content):
        """Put an object into S3"""
        try:
            self.s3_client.put_object(Bucket=bucket_name, Key=key, Body=content)
            return True
        except Exception as e:
            print(f"Error putting object to S3: {e}")
            return False

    def delete_object(self, bucket_name, key):
        """Delete an object from S3"""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
            return True
        except Exception as e:
            print(f"Error deleting object from S3: {e}")
            return False

    def move_object(self, bucket, source_key, dest_key):
        """Move an object within the same bucket using copy_object"""
        try:
            # Copy the object to the new location
            self.s3_client.copy_object(
                Bucket=bucket,
                CopySource={"Bucket": bucket, "Key": source_key},
                Key=dest_key,
            )
            # Delete the original object
            self.delete_object(bucket, source_key)
            return True
        except Exception as e:
            print(f"Error moving object from {source_key} to {dest_key}: {e}")
            return False


def create_s3_middleware(company_id=None, user_uuid=None):
    return S3Middleware(company_id, user_uuid)
