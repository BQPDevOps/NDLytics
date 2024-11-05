import boto3


class DynamoAdapter:
    """A wrapper class for AWS DynamoDB operations.

    Args:
        table_name (str): The name of the DynamoDB table to interact with.

    Example:
        dynamo = DynamoAdapter("my-table")
    """

    def __init__(self, table_name):
        self.dynamo_client = boto3.client("dynamodb")
        self.table_name = table_name

    def get_item(self, key):
        """Retrieve an item from DynamoDB by its key.

        Args:
            key (dict): The primary key of the item to retrieve.
                Example: {"user_id": {"S": "123"}}

        Returns:
            dict: The formatted item if found, None otherwise.

        Example:
            dynamo.get_item({"user_id": {"S": "123"}})
        """
        response = self.dynamo_client.get_item(TableName=self.table_name, Key=key)
        if "Item" not in response:
            return None

        item = response["Item"]
        formatted_item = {}

        for key, value in item.items():
            if "S" in value:  # String
                formatted_item[key] = value["S"]
            elif "N" in value:  # Number
                formatted_item[key] = float(value["N"])
            elif "BOOL" in value:  # Boolean
                formatted_item[key] = value["BOOL"]
            elif "L" in value:  # List
                formatted_item[key] = self._format_list(value["L"])
            elif "M" in value:  # Map
                formatted_item[key] = self._format_map(value["M"])
            # Add more type checks as needed

        return formatted_item

    def _format_list(self, dynamo_list):
        """Format a DynamoDB list into a Python list.

        Args:
            dynamo_list (list): The DynamoDB formatted list.

        Returns:
            list: A Python formatted list.

        Example:
            _format_list([{"S": "value1"}, {"N": "123"}])
            # Returns: ["value1", 123.0]
        """
        return [self._format_value(item) for item in dynamo_list]

    def _format_map(self, dynamo_map):
        """Format a DynamoDB map into a Python dictionary.

        Args:
            dynamo_map (dict): The DynamoDB formatted map.

        Returns:
            dict: A Python formatted dictionary.

        Example:
            _format_map({"key1": {"S": "value1"}, "key2": {"N": "123"}})
            # Returns: {"key1": "value1", "key2": 123.0}
        """
        return {k: self._format_value(v) for k, v in dynamo_map.items()}

    def _format_value(self, value):
        """Format a DynamoDB value into its Python equivalent.

        Args:
            value (dict): The DynamoDB formatted value.

        Returns:
            Any: The Python formatted value.

        Example:
            _format_value({"S": "hello"})  # Returns: "hello"
            _format_value({"N": "123"})    # Returns: 123.0
        """
        if "S" in value:
            return value["S"]
        elif "N" in value:
            return float(value["N"])
        elif "BOOL" in value:
            return value["BOOL"]
        elif "L" in value:
            return self._format_list(value["L"])
        elif "M" in value:
            return self._format_map(value["M"])
        # Add more type checks as needed
        return None

    def put_item(self, item):
        """Insert or replace an item in DynamoDB.

        Args:
            item (dict): The item to store in DynamoDB format.
                Example: {
                    "user_id": {"S": "123"},
                    "name": {"S": "John"},
                    "age": {"N": "30"}
                }

        Returns:
            dict: Response from DynamoDB if successful, None if error.

        Example:
            dynamo.put_item({
                "user_id": {"S": "123"},
                "name": {"S": "John"},
                "age": {"N": "30"}
            })
        """
        try:
            return self.dynamo_client.put_item(TableName=self.table_name, Item=item)
        except Exception as e:
            print(f"Error putting item: {e}")
            return None

    def update_item(
        self,
        key,
        update_expression,
        expression_attribute_values,
        expression_attribute_names=None,
    ):
        """Update an item in DynamoDB.

        Args:
            key (dict): The primary key of the item.
                Example: {"user_id": {"S": "123"}}
            update_expression (str): The update expression.
                Example: "SET #n = :name, age = :age"
            expression_attribute_values (dict): Values for the expression.
                Example: {":name": {"S": "John"}, ":age": {"N": "31"}}
            expression_attribute_names (dict, optional): Names for the expression.
                Example: {"#n": "name"}

        Returns:
            dict: Response from DynamoDB if successful, None if error.

        Example:
            dynamo.update_item(
                {"user_id": {"S": "123"}},
                "SET #n = :name, age = :age",
                {":name": {"S": "John"}, ":age": {"N": "31"}},
                {"#n": "name"}
            )
        """
        try:
            update_params = {
                "TableName": self.table_name,
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_attribute_values,
            }

            if expression_attribute_names:
                update_params["ExpressionAttributeNames"] = expression_attribute_names

            return self.dynamo_client.update_item(**update_params)
        except Exception as e:
            print(f"Error updating item: {e}")
            return None

    def delete_item(self, key):
        """Delete an item from DynamoDB.

        Args:
            key (dict): The primary key of the item to delete.
                Example: {"user_id": {"S": "123"}}

        Example:
            dynamo.delete_item({"user_id": {"S": "123"}})
        """
        self.dynamo_client.delete_item(TableName=self.table_name, Key=key)

    def query(
        self,
        key_condition_expression,
        expression_attribute_values,
        expression_attribute_names=None,
        index_name=None,
    ):
        """Query items from DynamoDB using a key condition expression.

        Args:
            key_condition_expression (str): The key condition expression.
                Example: "user_id = :uid"
            expression_attribute_values (dict): Values for the expression.
                Example: {":uid": {"S": "123"}}
            expression_attribute_names (dict, optional): Names for the expression.
                Example: {"#n": "name"}
            index_name (str, optional): Name of the index to query.

        Returns:
            list: List of matching items.

        Example:
            dynamo.query(
                "user_id = :uid",
                {":uid": {"S": "123"}},
                {"#n": "name"},
                "user_id-index"
            )
        """
        try:
            query_params = {
                "KeyConditionExpression": key_condition_expression,
                "ExpressionAttributeValues": expression_attribute_values,
            }
            if expression_attribute_names:
                query_params["ExpressionAttributeNames"] = (
                    expression_attribute_names  # Add to params
                )
            if index_name:
                query_params["IndexName"] = index_name

            response = self.dynamo_adapter.query(**query_params)
            return response.get("Items", [])  # Return the items directly
        except Exception as e:
            print(f"Error querying items: {e}")
            return []

    def scan(
        self,
        FilterExpression=None,
        ExpressionAttributeValues=None,
        ExpressionAttributeNames=None,
    ):
        """Scan the table with optional filter expressions.

        Args:
            FilterExpression (str, optional): The filter expression.
                Example: "age > :min_age"
            ExpressionAttributeValues (dict, optional): Values for the filter expression.
                Example: {":min_age": {"N": "18"}}
            ExpressionAttributeNames (dict, optional): Names for the filter expression.
                Example: {"#n": "name"}

        Returns:
            list: List of items matching the filter condition.

        Example:
            dynamo.scan(
                FilterExpression="age > :min_age",
                ExpressionAttributeValues={":min_age": {"N": "18"}},
                ExpressionAttributeNames={"#n": "name"}
            )
        """
        scan_params = {
            "TableName": self.table_name,
        }

        if FilterExpression:
            scan_params["FilterExpression"] = FilterExpression
        if ExpressionAttributeValues:
            scan_params["ExpressionAttributeValues"] = ExpressionAttributeValues
        if ExpressionAttributeNames:
            scan_params["ExpressionAttributeNames"] = ExpressionAttributeNames

        try:
            response = self.dynamo_client.scan(**scan_params)
            return response.get("Items", [])
        except Exception as e:
            print(f"Error scanning items: {e}")
            return []
