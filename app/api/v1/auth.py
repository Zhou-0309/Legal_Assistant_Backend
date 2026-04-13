from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.api.deps import require_service_auth
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.common import AuthLoginRequest, AuthLogoutResponse, AuthTokenResponse
from app.services.user_ids import normalize_user_id
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.models.user import User
from app.schemas.common import AuthLoginRequest, AuthLogoutResponse, AuthTokenResponse
from app.services.user_ids import normalize_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


def _create_access_token(settings: Settings, user_id: str) -> str:
    if not settings.jwt_secret:
        raise AppError(
            "jwt_not_configured",
            "未配置 JWT_SECRET",
            status_code=503,
        )
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=30)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: AuthLoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AuthTokenResponse:
    if not body.user_id and not body.phone:
        raise AppError(
            "invalid_request",
            "登录请求必须包含 user_id 或 phone",
            status_code=400,
        )

    if body.phone:
        result = await session.execute(select(User).where(User.phone == body.phone))
        user = result.scalar_one_or_none()
        if user is None:
            uid = normalize_user_id(body.phone, settings)
            user = User(
                id=uid,
                nickname=body.nickname or "用户",
                user_type="personal",
                phone=body.phone,
            )
            session.add(user)
            await session.flush()
        elif body.nickname and user.nickname == "用户":
            user.nickname = body.nickname
            await session.flush()
    else:
        uid = normalize_user_id(body.user_id, settings)
        result = await session.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=uid,
                nickname=body.nickname or "用户",
                user_type="personal",
                phone=None,
            )
            session.add(user)
            await session.flush()
        elif body.nickname and user.nickname == "用户":
            user.nickname = body.nickname
            await session.flush()

    token = _create_access_token(settings, user.id)
    return AuthTokenResponse(access_token=token, token_type="bearer", user_id=user.id)


@router.post("/logout", dependencies=[Depends(require_service_auth)], response_model=AuthLogoutResponse)
async def logout() -> AuthLogoutResponse:
    return AuthLogoutResponse(message="已登出")
