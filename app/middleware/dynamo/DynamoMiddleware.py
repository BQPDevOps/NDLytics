import boto3

"""
Example key format for DynamoDB operations:
{
    "id": {"S": "123"},
    "sort_key": {"S": "ABC"}
}

Example item format:
{
    "id": {"S": "123"},
    "sort_key": {"S": "ABC"},
    "field1": {"S": "value1"},
    "field2": {"N": "123"},
    "field3": {"BOOL": True}
}

Example update expression:
"SET field1 = :val1, field2 = :val2"

Example expression attribute values:
{
    ":val1": {"S": "new_value"},
    ":val2": {"N": "456"}
}
"""


class DynamoMiddleware:
    def __init__(self, table_name):
        self.dynamo_client = boto3.client("dynamodb")
        self.table_name = table_name

    def get_item(self, key):
        response = self.dynamo_client.get_item(TableName=self.table_name, Key=key)
        if "Item" not in response:
            return None

        return response["Item"]

    def get_all_items(self):
        response = self.dynamo_client.scan(TableName=self.table_name)
        return response["Items"]

    def put_item(self, item):
        response = self.dynamo_client.put_item(TableName=self.table_name, Item=item)
        return response

    def update_item(
        self,
        key,
        update_expression,
        expression_attribute_values,
        expression_attribute_names=None,
    ):
        params = {
            "TableName": self.table_name,
            "Key": key,
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attribute_values,
        }
        if expression_attribute_names:
            params["ExpressionAttributeNames"] = expression_attribute_names

        response = self.dynamo_client.update_item(**params)
        return response

    def delete_item(self, key):
        response = self.dynamo_client.delete_item(TableName=self.table_name, Key=key)
        return response

    def query(self, query_expression, expression_attribute_values):
        response = self.dynamo_client.query(
            TableName=self.table_name,
            QueryExpression=query_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )
        return response

    def scan(self, filter_expression=None, expression_attribute_values=None):
        params = {"TableName": self.table_name}

        if filter_expression:
            params["FilterExpression"] = filter_expression
        if expression_attribute_values:
            params["ExpressionAttributeValues"] = expression_attribute_values

        response = self.dynamo_client.scan(**params)
        return response


def create_dynamo_middleware(table_name):
    return DynamoMiddleware(table_name)
