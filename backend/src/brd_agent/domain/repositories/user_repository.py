import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from brd_agent.core.exceptions import AuthError
from brd_agent.core.security import hash_password
from brd_agent.domain.models.user import UserCreate, UserInDB, build_user_document


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db.users

    async def get_by_email(self, email: str) -> UserInDB | None:
        document = await self._collection.find_one({"email": email.lower()})
        if document is None:
            return None
        return UserInDB.model_validate(document)

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        document = await self._collection.find_one({"_id": user_id})
        if document is None:
            return None
        return UserInDB.model_validate(document)

    async def create(self, user_data: UserCreate) -> UserInDB:
        hashed_password = await hash_password(user_data.password)
        user_id = str(uuid.uuid4())
        document = build_user_document(
            user_id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )

        try:
            await self._collection.insert_one(document)
        except DuplicateKeyError:
            raise AuthError("Email already registered", status_code=409) from None

        return UserInDB.model_validate(document)
