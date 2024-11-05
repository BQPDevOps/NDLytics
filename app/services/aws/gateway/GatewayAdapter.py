from config import config
import requests
import json


from models import AccessToken


class GatewayAdapter:
    def __init__(self, storage):
        self.storage = storage
        self.api_endpoint = config.aws_api_invoke_url
        self.access_token = AccessToken(self.storage.get_from_storage("access_token"))

    def _send_request(self, payload):
        headers = {
            "access-token": self.access_token.get_encoded_token(),
            "Content-Type": "application/json",
        }
        response = requests.post(self.api_endpoint, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def _create_payload(self, route, payload={}, is_async=False):
        return {
            "access_token": self.access_token.get_encoded_token(),
            "route": route,
            "payload": payload,
            "is_async": is_async,
        }

    def get_dataset(self, dataset_name):
        payload = self._create_payload(route=f"fetch-dataset-{dataset_name}")
        response = self._send_request(payload)
        if response is not None:
            cleaned_response = json.loads(response["body"])
            return json.loads(cleaned_response["output"]["body"])
        else:
            return {
                "statusCode": 400,
                "message": "Failed to fetch dataset",
                "error": response,
            }
