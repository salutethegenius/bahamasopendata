"""FastAPI dependencies for authentication and authorization."""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token, hash_ingestion_api_key
from app.db.database import get_db
from app.db.models import AdminUser, AuditLog, IngestionApiKey

logger = logging.getLogger(__name__)


def get_access_token_optional(
    authorization: str | None = Header(None),
    access_cookie: str | None = Cookie(
        None,
        alias=settings.ACCESS_TOKEN_COOKIE_NAME,
    ),
) -> str | None:
    """Bearer header takes precedence; else httpOnly access cookie (R01)."""
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
            return parts[1]
    return access_cookie

ADMIN_ROLES = {"admin", "superuser"}
PANEL_ROLES = {"uploader", "admin", "superuser"}


@dataclass
class IngestionActor:
    """Authenticated actor for ingestion endpoints."""

    user: AdminUser | None = None
    api_key: IngestionApiKey | None = None

    @property
    def actor_type(self) -> str:
        if self.user:
            return "user"
        if self.api_key:
            return "api_key"
        return "unknown"

    @property
    def label(self) -> str:
        if self.user:
            return self.user.email
        if self.api_key:
            return f"api_key:{self.api_key.name}"
        return "unknown"

    @property
    def audit_user_id(self) -> int | None:
        if self.user:
            return self.user.id
        if self.api_key:
            return self.api_key.created_by_user_id
        return None

    @property
    def role(self) -> str | None:
        if self.user:
            return self.user.role
        return None

    def audit_details(self) -> dict[str, str | int | None]:
        details: dict[str, str | int | None] = {
            "actor_type": self.actor_type,
            "actor_label": self.label,
            "actor_role": self.role,
        }
        if self.user:
            details["user_email"] = self.user.email
            details["user_id"] = self.user.id
        if self.api_key:
            details["api_key_id"] = self.api_key.id
            details["api_key_name"] = self.api_key.name
            details["api_key_prefix"] = self.api_key.key_prefix
            details["api_key_created_by_user_id"] = self.api_key.created_by_user_id
        return details


def utc_now_naive() -> datetime:
    """Return UTC now as a naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _get_user_from_token(token: str | None, db: AsyncSession) -> AdminUser | None:
    """Resolve a bearer token into an active admin user."""
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
    except Exception:
        return None

    user_id = int(payload["sub"])
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    user = result.scalars().first()
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    token: str | None = Depends(get_access_token_optional),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Extract and validate the current user from the Bearer token."""
    user = await _get_user_from_token(token, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_staff_user(
    token: str | None = Depends(get_access_token_optional),
    db: AsyncSession = Depends(get_db),
) -> AdminUser | None:
    """Resolved admin user when a valid access cookie/header is present; else None."""
    if token is None:
        return None
    return await _get_user_from_token(token, db)


async def require_superuser(
    user: AdminUser = Depends(get_current_user),
) -> AdminUser:
    """Require the current user to be a superuser."""
    if user.role != "superuser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return user


async def require_admin(
    user: AdminUser = Depends(get_current_user),
) -> AdminUser:
    """Require the current user to be an admin or superuser."""
    if user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_panel_user(
    user: AdminUser = Depends(get_current_user),
) -> AdminUser:
    """Require a user who can access the admin panel collections workflow."""
    if user.role not in PANEL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Panel access required",
        )
    return user


async def get_current_ingestion_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> IngestionApiKey | None:
    """Resolve an X-API-Key header into an active ingestion API key."""
    if not x_api_key:
        return None

    result = await db.execute(
        select(IngestionApiKey).where(
            IngestionApiKey.key_hash == hash_ingestion_api_key(x_api_key),
            IngestionApiKey.is_active.is_(True),
            IngestionApiKey.revoked_at.is_(None),
        )
    )
    return result.scalars().first()


async def require_ingestion_access(
    token: str | None = Depends(get_access_token_optional),
    db: AsyncSession = Depends(get_db),
    api_key: IngestionApiKey | None = Depends(get_current_ingestion_api_key),
) -> IngestionActor:
    """Allow either admin JWT auth or an active ingestion API key."""
    user = await _get_user_from_token(token, db)
    if user is not None:
        if user.role not in ADMIN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return IngestionActor(user=user)

    if api_key is not None:
        return IngestionActor(api_key=api_key)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_document_access(
    token: str | None = Depends(get_access_token_optional),
    db: AsyncSession = Depends(get_db),
    api_key: IngestionApiKey | None = Depends(get_current_ingestion_api_key),
) -> IngestionActor:
    """Allow panel users or ingestion API keys to work with documents."""
    user = await _get_user_from_token(token, db)
    if user is not None:
        if user.role not in PANEL_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Document access required",
            )
        return IngestionActor(user=user)

    if api_key is not None:
        return IngestionActor(api_key=api_key)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For only when behind a trusted proxy.

    TRUSTED_PROXY_COUNT controls how many proxies sit in front of the app.
    When 0 (default), X-Forwarded-For is ignored to prevent spoofing.
    When > 0, the Nth-from-right entry is used (the one your outermost
    trusted proxy appended).
    """
    proxy_count = settings.TRUSTED_PROXY_COUNT
    if proxy_count > 0:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",")]
            # Take the entry added by the outermost trusted proxy
            index = max(0, len(parts) - proxy_count)
            return parts[index]
    return request.client.host if request.client else "unknown"


def _build_audit_log_fn(
    actor: IngestionActor,
    ip: str,
    db: AsyncSession,
) -> Callable:
    """Build an audit-logging callable for the given actor and request."""

    async def log(
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        serialized_resource_id = None
        if resource_id is not None:
            serialized_resource_id = str(resource_id)
            if len(serialized_resource_id) > 50:
                details = {
                    **(details or {}),
                    "resource_id_full": serialized_resource_id,
                }
                serialized_resource_id = serialized_resource_id[:50]

        enriched_details = {
            **(details or {}),
            **actor.audit_details(),
        }
        if actor.api_key:
            actor.api_key.last_used_at = utc_now_naive()

        entry = AuditLog(
            user_id=actor.audit_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=serialized_resource_id,
            details=enriched_details,
            ip_address=ip,
        )
        db.add(entry)
        await db.flush()

    return log


async def get_audit_logger(
    request: Request,
    user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Callable:
    """Returns a callable to log audit events for the current request."""
    return _build_audit_log_fn(IngestionActor(user=user), get_client_ip(request), db)


async def get_ingestion_audit_logger(
    request: Request,
    actor: IngestionActor = Depends(require_ingestion_access),
    db: AsyncSession = Depends(get_db),
) -> Callable:
    """Audit logger that works for both JWT admins and ingestion API keys."""
    return _build_audit_log_fn(actor, get_client_ip(request), db)


async def get_document_audit_logger(
    request: Request,
    actor: IngestionActor = Depends(require_document_access),
    db: AsyncSession = Depends(get_db),
) -> Callable:
    """Audit logger for document actions available to panel users or API keys."""
    return _build_audit_log_fn(actor, get_client_ip(request), db)
