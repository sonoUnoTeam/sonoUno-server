"""User Pydantic and Document models.
"""

# pylint: disable=too-few-public-methods

from datetime import datetime

from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr


class UserAuth(BaseModel):
    """User register and login auth"""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Updatable user fields"""

    email: EmailStr | None = None

    # User information
    first_name: str | None = None
    last_name: str | None = None


class UserOut(UserUpdate):
    """User fields returned to the client"""

    email: Indexed(EmailStr, unique=True)
    disabled: bool = False


class User(UserOut, Document):
    """User DB representation"""

    password: str
    email_confirmed_at: datetime | None = None

    def __repr__(self) -> str:
        return f'<User {self.email}>'

    def __str__(self) -> str:
        return self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, User):
            return self.email == other.email
        return False

    @property
    def created_at(self) -> datetime:
        """Datetime user was created from ID"""
        return self.id.generation_time

    @classmethod
    async def by_email(cls, email: str) -> 'User':
        """Get a user by email"""
        return await cls.find_one(cls.email == email)
