"""FastAPI server configuration.
"""

from typing import cast

from decouple import Undefined, config, undefined
from pydantic import BaseModel


def config_bool(name: str, default: bool | Undefined = undefined) -> bool:
    """Boolean config variable."""
    return cast(bool, config(name, cast=bool, default=default))


def config_int(name: str, default: int | Undefined = undefined) -> int:
    """Integer config variable."""
    return cast(int, config(name, cast=int, default=default))


def config_str(name: str, default: str | Undefined = undefined) -> str:
    """String config variable."""
    return cast(str, config(name, cast=str, default=default))


class Settings(BaseModel):
    """Server config settings."""

    server_name = config_str('SERVER_NAME')
    server_host = config_str('SERVER_HOST')

    # Mongo Engine settings
    mongo_database = config_str('MONGO_INITDB_DATABASE')
    mongo_uri = f'mongodb://{config("MONGO_INITDB_USERNAME")}:{config("MONGO_INITDB_PASSWORD")}@mongodb:27017/{config("MONGO_INITDB_DATABASE")}'  # noqa

    # Security settings
    authjwt_secret_key = config_str('SECRET_KEY')
    salt = config_str('SALT')

    # FastMail SMTP server settings
    mail_console = config_bool('MAIL_CONSOLE', default=False)
    mail_server = config_str('MAIL_SERVER', default='smtp.myserver.io')
    mail_port = config_int('MAIL_PORT', default=587)
    mail_username = config_str('MAIL_USERNAME')
    mail_password = config_str('MAIL_PASSWORD')
    mail_sender = config_str('MAIL_SENDER', default='noreply@myserver.io')

    # Minio
    minio_endpoint = config_str('MINIO_ENDPOINT')
    minio_access_key = config_str('MINIO_ACCESS_KEY')
    minio_secret_key = config_str('MINIO_SECRET_KEY')

    testing = config_bool('TESTING', default=False)


CONFIG = Settings()
