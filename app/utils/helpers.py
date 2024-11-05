from typing import Dict, List


class S3Adapter:
    def list_objects(self, bucket_name: str, current_path: str) -> Dict[str, List[str]]:
        """List objects in the S3 bucket at the current path"""
        try:
            # Ensure the path ends with a slash for proper prefix matching
            prefix = current_path if current_path.endswith("/") else f"{current_path}/"

            # Get objects from S3
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name, Prefix=prefix, Delimiter="/"
            )

            # Initialize results
            result = {"directories": [], "files": []}

            # Process common prefixes (directories)
            if "CommonPrefixes" in response:
                result["directories"].extend(
                    p["Prefix"] for p in response["CommonPrefixes"]
                )

            # Process contents (files)
            if "Contents" in response:
                for obj in response["Contents"]:
                    # Skip if the object is the directory itself
                    if obj["Key"] == prefix:
                        continue
                    # Skip if the object is in a subdirectory
                    if "/" in obj["Key"][len(prefix) :]:
                        continue
                    result["files"].append(obj["Key"])

            return result

        except Exception as e:
            print(f"Error listing objects: {str(e)}")
            return {"directories": [], "files": []}


def dynamo_adapter(storage_manager):
    """Create a DynamoDB adapter instance with the correct table name"""
    from services.aws.dynamo import DynamoAdapter

    # Use the settings table name from the storage manager
    table_name = "NDA_Settings_Table"  # Hardcoded based on notepad context
    return DynamoAdapter(table_name)
