from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserInDB(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    email: EmailStr
    full_name: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_db(cls, user: UserInDB) -> "UserPublic":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )


def build_user_document(
    user_id: str,
    email: str,
    full_name: str,
    hashed_password: str,
) -> dict:
    now = datetime.now(UTC)
    return {
        "_id": user_id,
        "email": email.lower(),
        "full_name": full_name,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
