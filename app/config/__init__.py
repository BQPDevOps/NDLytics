from pydantic_settings import BaseSettings
from pathlib import Path


class Config(BaseSettings):
    # BOTO 3
    aws_access_key: str
    aws_secret_key: str
    aws_region: str

    # AWS COGNITO
    aws_cognito_user_pool_id: str
    aws_cognito_client_id: str

    # AWS DYNAMO DB
    aws_sessions_table_name: str
    aws_tasks_table_name: str
    aws_tickets_table_name: str
    aws_users_table_name: str
    aws_settings_table_name: str
    aws_companies_table_name: str

    # AWS S3 STORAGE
    aws_nda_storage_bucket: str
    aws_s3_deprecated_bucket: str
    aws_s3_system_bucket: str
    aws_s3_client_bucket: str
    aws_s3_tenant_storage_bucket: str

    # 3RD PARTY API KEYS
    api_key_openai: str
    api_key_pandasai: str
    api_key_langchain: str
    api_key_tavily: str
    api_key_groq: str
    api_key_nomic: str
    token_tcn: str

    # 3RD PARTY API BASE URLS
    base_url_tcn: str

    # N8N WEBHOOKS
    n8n_get_task_group_status_webhook: str
    n8n_get_outbound_reporting_webhook: str
    n8n_write_to_csv_stopgap_webhook: str
    n8n_get_from_csv_stopgap_webhook: str

    # FRAMEWORK
    app_storage_secret: str
    app_reload: bool
    app_port: int
    app_name: str

    # Docker
    compose_project_name: str

    class Config:
        case_sensitive = False
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        env_prefix = ""


config = Config()
