"""IAM response models.
"""

from datetime import timedelta

from pydantic import BaseModel
from pydantic import Field as F


class AccessToken(BaseModel):
    """Access token details"""

    access_token: str = F(title='Access token.')
    access_token_expires: timedelta = F(
        timedelta(minutes=15), title='Access token expiration, in seconds.'
    )

    class Config:
        schema_extra = {
            'description': 'Access token, returned upon user refresh.',
            'examples': [
                {
                    'access_token': 'eyJ0eXAiOiJKR1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0X2VtYWlsQHRlc3QuY29tIiwiaWF0IjoxNjUzNTQxODAyLCJuYmYiOjE2NTM1NDE4MDIsImp0aSI6ImY5OGJlNTNjLTM0Y2MtNDdhMy04OWYwLTBkZjMyYjJkNmFkZiIsImV4cCI6MTY1MzU0MjcwMiwidHlwZSI6ImFjY2VzcyIsImZyZXNoIjpmYWxzZX0.BBMylO1JO84zEJ8hJbC_ckm-VwCT2C__v0z5wu3kvBg',  # noqa: E501
                    'access_token_expires': 900.0,
                }
            ],
        }


class RefreshToken(AccessToken):
    """Access and refresh token details"""

    refresh_token: str = F(title='Refresh token.')
    refresh_token_expires: timedelta = F(
        timedelta(days=30), title='Refresh token expiration, in seconds.'
    )

    class Config:
        schema_extra = {
            'description': 'An access and refresh token, returned upon user login.',
            'examples': [
                {
                    'access_token': 'eyJ0eXAiOiJKR1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0X2VtYWlsQHRlc3QuY29tIiwiaWF0IjoxNjUzNTQxODAyLCJuYmYiOjE2NTM1NDE4MDIsImp0aSI6ImY5OGJlNTNjLTM0Y2MtNDdhMy04OWYwLTBkZjMyYjJkNmFkZiIsImV4cCI6MTY1MzU0MjcwMiwidHlwZSI6ImFjY2VzcyIsImZyZXNoIjpmYWxzZX0.BBMylO1JO84zEJ8hJbC_ckm-VwCT2C__v0z5wu3kvBg',  # noqa: E501
                    'access_token_expires': 900.0,
                    'refresh_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN1X2VtYWlsQHRlc3QuY29tIiwiaWF0IjoxNjUzNTQxODAyLCJuYmYiOjE2NTM1NDE4MDIsImp0aSI6IjFhZmIxNmE0LWU4ZjUtNGQzMC1iODg3LTk3ZjcwNjI1MWI0YyIsImV4cCI6MTY1NjEzMzgwMiwidHlwZSI6InJlZnJlc2gifQ.9DP4GKLT9IWDE7qeNoxtKESCSJ8YnYEEF163UgYnBE0',  # noqa: E501
                    'refresh_token_expires': 2592000.0,
                }
            ],
        }
