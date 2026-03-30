"""Authentication API endpoints for admin users."""
import json
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import limiter, settings
from app.core.deps import get_client_ip, get_current_user, require_admin, utc_now_naive
from app.core.security import (
    create_access_token,
    create_ingestion_api_key,
    create_refresh_token,
    hash_refresh_token,
    hash_password,
    validate_password,
    verify_password,
)
from app.db.database import get_db
from app.db.models import AdminUser, AuditLog, IngestionApiKey, RefreshToken


router = APIRouter()

REFRESH_COOKIE_NAME = "refresh_token"


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserProfile(BaseModel):
    """Current user profile."""

    id: int
    email: str
    full_name: str | None = None
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    """Authentication response with short-lived access token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class ApiKeyCreateRequest(BaseModel):
    """Create a long-lived ingestion API key."""

    name: str = Field(..., min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ApiKeyRecord(BaseModel):
    """Safe API key metadata returned to the admin UI."""

    id: int
    name: str
    description: str | None = None
    key_prefix: str
    is_active: bool
    created_at: str | None = None
    last_used_at: str | None = None
    revoked_at: str | None = None


class ApiKeyCreateResponse(BaseModel):
    """Created API key metadata plus the raw key shown once."""

    api_key: str
    record: ApiKeyRecord


class UserCreateRequest(BaseModel):
    """Create a panel user."""

    email: EmailStr
    password: str = Field(..., min_length=12)
    full_name: str | None = Field(default=None, max_length=255)


class UserRecord(BaseModel):
    """Safe user payload for the admin access screen."""

    id: int
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: str | None = None
    last_login_at: str | None = None


class AuditLogRecord(BaseModel):
    """Audit event returned to the admin access screen."""

    id: int
    action: str
    resource_type: str
    resource_id: str | None = None
    actor_label: str
    actor_role: str | None = None
    actor_type: str
    ip_address: str | None = None
    created_at: str | None = None
    details: dict | None = None


async def _create_login_response(
    *,
    user: AdminUser,
    response: Response,
    request: Request,
    db: AsyncSession,
) -> LoginResponse:
    """Create token pair, persist refresh token hash, and set cookie."""
    access_token = create_access_token(user.id, user.role)
    raw_refresh_token, refresh_hash = create_refresh_token()
    ip_address = get_client_ip(request)
    expires_at = utc_now_naive() + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            ip_address=ip_address,
        )
    )

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=f"{settings.API_V1_PREFIX}/auth",
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate admin user and issue access/refresh tokens."""
    result = await db.execute(select(AdminUser).where(AdminUser.email == payload.email.lower()))
    user = result.scalars().first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    user.last_login_at = utc_now_naive()

    login_response = await _create_login_response(
        user=user,
        response=response,
        request=request,
        db=db,
    )

    db.add(
        AuditLog(
            user_id=user.id,
            action="login",
            resource_type="auth",
            details={"method": "password"},
            ip_address=get_client_ip(request),
        )
    )
    await db.commit()

    return login_response


@router.post("/refresh", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Rotate refresh token and return a new access token."""
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken, AdminUser)
        .join(AdminUser, AdminUser.id == RefreshToken.user_id)
        .where(RefreshToken.token_hash == token_hash)
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_record, user = row
    now = utc_now_naive()
    expires_at = token_record.expires_at

    if token_record.revoked_at is not None or expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    token_record.revoked_at = now

    login_response = await _create_login_response(
        user=user,
        response=response,
        request=request,
        db=db,
    )

    await db.commit()

    return login_response


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke current refresh token and clear refresh cookie."""
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_refresh_token:
        token_hash = hash_refresh_token(raw_refresh_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token_record = result.scalars().first()
        if token_record and token_record.revoked_at is None:
            token_record.revoked_at = utc_now_naive()

            db.add(
                AuditLog(
                    user_id=token_record.user_id,
                    action="logout",
                    resource_type="auth",
                    details={"revoked": True},
                    ip_address=get_client_ip(request),
                )
            )
            await db.commit()

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=f"{settings.API_V1_PREFIX}/auth",
    )
    return {"message": "Logged out"}


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: AdminUser = Depends(get_current_user)) -> UserProfile:
    """Return current authenticated user profile."""
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
    )


def serialize_api_key_record(record: IngestionApiKey) -> ApiKeyRecord:
    """Convert an API key row into a safe response payload."""
    return ApiKeyRecord(
        id=record.id,
        name=record.name,
        description=record.description,
        key_prefix=record.key_prefix,
        is_active=record.is_active,
        created_at=record.created_at.isoformat() if record.created_at else None,
        last_used_at=record.last_used_at.isoformat() if record.last_used_at else None,
        revoked_at=record.revoked_at.isoformat() if record.revoked_at else None,
    )


def serialize_user_record(record: AdminUser) -> UserRecord:
    """Convert a user row into a safe response payload."""
    return UserRecord(
        id=record.id,
        email=record.email,
        full_name=record.full_name,
        role=record.role,
        is_active=record.is_active,
        created_at=record.created_at.isoformat() if record.created_at else None,
        last_login_at=record.last_login_at.isoformat() if record.last_login_at else None,
    )


def serialize_audit_log_record(
    record: AuditLog,
    user: AdminUser | None = None,
) -> AuditLogRecord:
    """Convert an audit log row into a front-end payload."""
    details = record.details or {}
    actor_type = details.get("actor_type") or (
        "user" if user else "unknown"
    )
    actor_label = details.get("actor_label") or (
        user.email if user else "unknown"
    )
    actor_role = details.get("actor_role")
    if actor_role is None and actor_type == "user" and user:
        actor_role = user.role
    return AuditLogRecord(
        id=record.id,
        action=record.action,
        resource_type=record.resource_type,
        resource_id=record.resource_id,
        actor_label=str(actor_label),
        actor_role=str(actor_role) if actor_role is not None else None,
        actor_type=str(actor_type),
        ip_address=record.ip_address,
        created_at=record.created_at.isoformat() if record.created_at else None,
        details=details,
    )


def matches_audit_log_filters(
    record: AuditLogRecord,
    *,
    search: str | None = None,
    action: str | None = None,
    actor_type: str | None = None,
) -> bool:
    """Return whether a serialized audit record matches the requested filters."""
    normalized_action = action.strip().lower() if action else None
    normalized_actor_type = actor_type.strip().lower() if actor_type else None
    normalized_search = search.strip().lower() if search else None

    if normalized_action and record.action.lower() != normalized_action:
        return False

    if normalized_actor_type and record.actor_type.lower() != normalized_actor_type:
        return False

    if not normalized_search:
        return True

    haystack_parts: list[str] = [
        record.action,
        record.resource_type,
        record.resource_id or "",
        record.actor_label,
        record.actor_role or "",
        record.actor_type,
        record.ip_address or "",
    ]
    if record.details:
        haystack_parts.append(json.dumps(record.details, sort_keys=True))

    haystack = " ".join(haystack_parts).lower()
    return normalized_search in haystack


@router.get("/api-keys", response_model=list[ApiKeyRecord])
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def list_api_keys(
    request: Request,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyRecord]:
    """List ingestion API keys available to the current admin."""
    del request
    result = await db.execute(
        select(IngestionApiKey).order_by(IngestionApiKey.created_at.desc())
    )
    return [serialize_api_key_record(record) for record in result.scalars().all()]


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    request: Request,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    """Create an ingestion API key and return the raw token once."""
    raw_key, key_prefix, key_hash = create_ingestion_api_key()
    record = IngestionApiKey(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_by_user_id=current_user.id,
        is_active=True,
    )
    db.add(record)
    await db.flush()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=str(record.id),
            details={
                "name": record.name,
                "key_prefix": record.key_prefix,
            },
            ip_address=get_client_ip(request),
        )
    )
    await db.commit()
    await db.refresh(record)
    return ApiKeyCreateResponse(api_key=raw_key, record=serialize_api_key_record(record))


@router.post("/api-keys/{key_id}/revoke", response_model=ApiKeyRecord)
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def revoke_api_key(
    key_id: int,
    request: Request,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyRecord:
    """Revoke an ingestion API key."""
    result = await db.execute(select(IngestionApiKey).where(IngestionApiKey.id == key_id))
    record = result.scalars().first()
    if record is None:
        raise HTTPException(status_code=404, detail="API key not found")

    record.is_active = False
    record.revoked_at = utc_now_naive()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=str(record.id),
            details={
                "name": record.name,
                "key_prefix": record.key_prefix,
            },
            ip_address=get_client_ip(request),
        )
    )
    await db.commit()
    await db.refresh(record)
    return serialize_api_key_record(record)


@router.get("/users", response_model=list[UserRecord])
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def list_users(
    request: Request,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserRecord]:
    """List panel users available to the current admin."""
    del request
    del current_user
    result = await db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
    return [serialize_user_record(record) for record in result.scalars().all()]


@router.post("/users", response_model=UserRecord, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRecord:
    """Create a new panel user."""
    email = payload.email.lower()
    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists",
        )

    try:
        validate_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = AdminUser(
        email=email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip() if payload.full_name else None,
        role="uploader",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="create_user",
            resource_type="user",
            resource_id=str(user.id),
            details={
                "created_user_email": user.email,
                "created_user_role": "uploader",
                "actor_type": "user",
                "actor_label": current_user.email,
                "actor_role": current_user.role,
                "user_email": current_user.email,
                "user_id": current_user.id,
            },
            ip_address=get_client_ip(request),
        )
    )
    await db.commit()
    await db.refresh(user)
    return serialize_user_record(user)


@router.post("/users/{user_id}/revoke", response_model=UserRecord)
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def revoke_user_access(
    user_id: int,
    request: Request,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserRecord:
    """Disable an uploader account."""
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot revoke your own access",
        )

    if user.role != "uploader":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only uploader accounts can be revoked here",
        )

    user.is_active = False
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="revoke_user_access",
            resource_type="user",
            resource_id=str(user.id),
            details={
                "revoked_user_email": user.email,
                "revoked_user_role": user.role,
                "actor_type": "user",
                "actor_label": current_user.email,
                "actor_role": current_user.role,
                "user_email": current_user.email,
                "user_id": current_user.id,
            },
            ip_address=get_client_ip(request),
        )
    )
    await db.commit()
    await db.refresh(user)
    return serialize_user_record(user)


@router.get("/audit-log", response_model=list[AuditLogRecord])
@limiter.limit(settings.RATE_LIMIT_ADMIN)
async def list_audit_log(
    request: Request,
    limit: int = 50,
    search: str | None = None,
    action: str | None = None,
    actor_type: str | None = None,
    current_user: AdminUser = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogRecord]:
    """Return recent access and ingestion activity."""
    del request
    del current_user
    safe_limit = max(1, min(limit, 200))
    fetch_limit = 500 if search or action or actor_type else safe_limit
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(fetch_limit)
    )
    records = result.scalars().all()
    user_ids = list({record.user_id for record in records if record.user_id})
    users_by_id: dict[int, AdminUser] = {}
    if user_ids:
        user_result = await db.execute(
            select(AdminUser).where(AdminUser.id.in_(user_ids))
        )
        users_by_id = {user.id: user for user in user_result.scalars().all()}

    serialized_records = [
        serialize_audit_log_record(record, users_by_id.get(record.user_id))
        for record in records
    ]
    filtered_records = [
        record
        for record in serialized_records
        if matches_audit_log_filters(
            record,
            search=search,
            action=action,
            actor_type=actor_type,
        )
    ]
    return filtered_records[:safe_limit]
