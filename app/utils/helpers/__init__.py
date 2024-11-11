from config import config
from services.aws.cognito import CognitoAdapter
from services.aws.s3 import S3StorageAdapter, S3MLMAdapter
from services.aws.dynamo import DynamoAdapter
from services.aws.gateway import GatewayAdapter
from services.tcn.TCNAdapter import TCNAdapter

from models import IDToken


def cognito_adapter():
    return CognitoAdapter(
        config.aws_cognito_user_pool_id,
        config.aws_cognito_client_id,
        config.aws_region,
        config.aws_sessions_table_name,
    )


def s3_storage_adapter(storage_instance):
    id_token = IDToken(storage_instance.get_from_storage("id_token"))
    decoded_token = id_token.get_decoded_token()
    company_id = decoded_token.get("custom:company_id")
    user_uuid = decoded_token.get("sub")
    return S3StorageAdapter(company_id, user_uuid)


def s3_mlm_adapter(bucket_name):
    return S3MLMAdapter(bucket_name)


def gateway_adapter(storage_instance):
    return GatewayAdapter(storage_instance)


def dynamo_adapter(table_name):
    return DynamoAdapter(table_name)


def tcn_adapter():
    return TCNAdapter(config.base_url_tcn, config.token_tcn)


__all__ = [
    "cognito_adapter",
    "s3_storage_adapter",
    "s3_mlm_adapter",
    "gateway_adapter",
    "dynamo_adapter",
    "tcn_adapter",
]
