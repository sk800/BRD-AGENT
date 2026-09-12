from motor.motor_asyncio import AsyncIOMotorDatabase

from brd_agent.core.exceptions import AuthError
from brd_agent.core.security import create_access_token, verify_password
from brd_agent.domain.models.user import UserCreate, UserInDB, UserPublic
from brd_agent.domain.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._users = UserRepository(db)

    async def signup(self, user_data: UserCreate) -> UserPublic:
        existing_user = await self._users.get_by_email(user_data.email)
        if existing_user is not None:
            raise AuthError("Email already registered", status_code=409)

        user = await self._users.create(user_data)
        return UserPublic.from_db(user) 

    async def login(self, email: str, password: str) -> tuple[UserPublic, str]:
        user = await self._users.get_by_email(email)
        if user is None:
            raise AuthError("Invalid email or password", status_code=401)

        if not user.is_active:
            raise AuthError("Account is inactive", status_code=403)

        password_valid = await verify_password(password, user.hashed_password)
        if not password_valid:
            raise AuthError("Invalid email or password", status_code=401)

        token = create_access_token(user.id)
        return UserPublic.from_db(user), token

    async def get_user_by_id(self, user_id: str) -> UserInDB | None:
        return await self._users.get_by_id(user_id)
