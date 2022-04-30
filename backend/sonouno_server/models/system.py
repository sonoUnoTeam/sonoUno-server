from pydantic import BaseModel


class SystemInfo(BaseModel):
    backend_version: str
