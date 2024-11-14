from pydantic_settings import BaseSettings
from pathlib import Path


class Config(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_cognito_user_pool_id: str
    aws_cognito_client_id: str
    aws_region: str
    aws_sessions_table_name: str
    aws_users_table_name: str
    aws_clients_table_name: str
    aws_general_table_name: str
    aws_requests_table_name: str
    aws_companies_table_name: str
    aws_acl_table_name: str
    aws_task_log_table_name: str
    aws_api_invoke_url: str
    aws_s3_deprecated_bucket: str
    aws_s3_system_bucket: str
    aws_s3_client_bucket: str
    base_url_tcn: str
    token_tcn: str
    api_key_openai: str
    api_key_pandasai: str
    api_key_langchain: str
    tavily_api_key: str
    app_storage_secret: str
    app_reload: bool
    app_port: int
    app_name: str
    token_github: str
    groq_api_key: str
    nomic_api_key: str
    aws_settings_table_name: str
    aws_tickets_table_name: str

    class Config:
        case_sensitive = False
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        env_file_encoding = "utf-8"
        env_prefix = ""


config = Config()
