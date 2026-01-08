import os
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class AWSConfig:
    """Configurações AWS carregadas do arquivo .env"""

    @staticmethod
    def get_access_key_id() -> str:
        """Retorna AWS Access Key ID"""
        return os.getenv('AWS_ACCESS_KEY_ID', '')

    @staticmethod
    def get_secret_access_key() -> str:
        """Retorna AWS Secret Access Key"""
        return os.getenv('AWS_SECRET_ACCESS_KEY', '')

    @staticmethod
    def get_session_token() -> str:
        """Retorna AWS Session Token (opcional)"""
        return os.getenv('AWS_SESSION_TOKEN', '')

    @staticmethod
    def get_region() -> str:
        """Retorna região AWS"""
        return os.getenv('AWS_REGION', 'eu-west-1')

    @staticmethod
    def get_profile() -> str:
        """Retorna profile AWS CLI (opcional)"""
        return os.getenv('AWS_PROFILE', '')

    @staticmethod
    def get_dynamodb_table_name() -> str:
        """Retorna nome da tabela DynamoDB"""
        return os.getenv('DYNAMODB_TABLE_NAME', 'dcxstg-dev-converter-work-pool')

    @staticmethod
    def has_credentials() -> bool:
        """Verifica se há credenciais configuradas"""
        return bool(
            (AWSConfig.get_access_key_id() and AWSConfig.get_secret_access_key()) or
            AWSConfig.get_profile()
        )

    @staticmethod
    def get_auth_method() -> str:
        """Retorna método de autenticação preferido"""
        if AWSConfig.get_profile():
            return 'profile'
        elif AWSConfig.get_access_key_id() and AWSConfig.get_secret_access_key():
            return 'credentials'
        else:
            return 'env_vars'
