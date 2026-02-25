"""Polls API endpoints."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Poll, PollOption, PollVote


router = APIRouter()


class PollOptionCreate(BaseModel):
    """Poll option payload."""

    option_text: str = Field(..., max_length=255)
    display_order: int = 0


class PollCreate(BaseModel):
    """Create a new poll with options."""

    question: str = Field(..., max_length=500)
    description: Optional[str] = None
    status: str = "draft"  # "draft", "active", "closed"
    domain: Optional[str] = None  # "budget", "health", "income", etc.
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    options: List[PollOptionCreate]


class PollUpdate(BaseModel):
    """Update an existing poll."""

    question: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None
    domain: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PollOptionResult(BaseModel):
    """Poll option with aggregated votes."""

    id: int
    option_text: str
    display_order: int
    votes: int


class PollResult(BaseModel):
    """Poll with aggregated results."""

    id: int
    question: str
    description: Optional[str]
    status: str
    domain: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    total_votes: int
    options: List[PollOptionResult]


class VoteRequest(BaseModel):
    """Request payload for casting a vote."""

    option_id: int
    fingerprint: Optional[str] = None


def _aggregate_poll_result(
    poll: Poll,
    option_rows: List[PollOption],
    vote_counts: dict[int, int],
) -> PollResult:
    total_votes = sum(vote_counts.values())
    options_out: List[PollOptionResult] = []

    for opt in sorted(option_rows, key=lambda o: o.display_order):
        votes = vote_counts.get(opt.id, 0)
        options_out.append(
            PollOptionResult(
                id=opt.id,
                option_text=opt.option_text,
                display_order=opt.display_order,
                votes=votes,
            )
        )

    return PollResult(
        id=poll.id,
        question=poll.question,
        description=poll.description,
        status=poll.status,
        domain=poll.domain,
        start_date=poll.start_date,
        end_date=poll.end_date,
        total_votes=total_votes,
        options=options_out,
    )


async def _load_poll_with_results(
    poll: Poll,
    db: AsyncSession,
) -> PollResult:
    options_result = await db.execute(
        select(PollOption).where(PollOption.poll_id == poll.id)
    )
    option_rows = list(options_result.scalars().all())

    votes_result = await db.execute(
        select(PollVote.option_id, func.count(PollVote.id))
        .where(PollVote.poll_id == poll.id)
        .group_by(PollVote.option_id)
    )
    vote_counts = {row[0]: row[1] for row in votes_result.all()}

    return _aggregate_poll_result(poll, option_rows, vote_counts)


def _require_admin(api_key: Optional[str], expected: Optional[str]) -> None:
    """Simple API key check for admin endpoints."""
    if not expected:
        # If no admin key configured, treat all access as admin (development mode).
        return
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid admin API key")


@router.get("", response_model=List[PollResult])
async def list_polls(db: AsyncSession = Depends(get_db)) -> List[PollResult]:
    """
    List all polls with aggregated results, newest first.
    Includes both active and recently closed polls.
    """
    result = await db.execute(
        select(Poll).order_by(Poll.created_at.desc())
    )
    polls = result.scalars().all()

    output: List[PollResult] = []
    for poll in polls:
        output.append(await _load_poll_with_results(poll, db))
    return output


@router.get("/active", response_model=Optional[PollResult])
async def get_active_poll(db: AsyncSession = Depends(get_db)) -> Optional[PollResult]:
    """Get the currently active poll, if any."""
    result = await db.execute(
        select(Poll)
            .where(Poll.status == "active")
            .order_by(Poll.start_date.desc().nullslast(), Poll.created_at.desc())
            .limit(1)
    )
    poll = result.scalars().first()
    if not poll:
        return None
    return await _load_poll_with_results(poll, db)


@router.get("/{poll_id}", response_model=PollResult)
async def get_poll(poll_id: int, db: AsyncSession = Depends(get_db)) -> PollResult:
    """Get a specific poll by ID with results."""
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalars().first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return await _load_poll_with_results(poll, db)


@router.post("", response_model=PollResult)
async def create_poll(
    payload: PollCreate,
    db: AsyncSession = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(default=None),
) -> PollResult:
    """
    Create a new poll.

    Admin-only: requires X-Admin-Api-Key header when POLLS_ADMIN_API_KEY is set.
    """
    from app.core.config import settings  # local import to avoid cycles

    _require_admin(x_admin_api_key, getattr(settings, "POLLS_ADMIN_API_KEY", None))

    poll = Poll(
        question=payload.question,
        description=payload.description,
        status=payload.status or "draft",
        domain=payload.domain,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(poll)
    await db.flush()

    for opt in payload.options:
        option = PollOption(
            poll_id=poll.id,
            option_text=opt.option_text,
            display_order=opt.display_order,
        )
        db.add(option)

    await db.commit()
    await db.refresh(poll)

    return await _load_poll_with_results(poll, db)


@router.patch("/{poll_id}", response_model=PollResult)
async def update_poll(
    poll_id: int,
    payload: PollUpdate,
    db: AsyncSession = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(default=None),
) -> PollResult:
    """Update poll metadata (question, description, status, dates, domain)."""
    from app.core.config import settings

    _require_admin(x_admin_api_key, getattr(settings, "POLLS_ADMIN_API_KEY", None))

    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalars().first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(poll, field, value)

    await db.commit()
    await db.refresh(poll)
    return await _load_poll_with_results(poll, db)


@router.delete("/{poll_id}", status_code=204)
async def delete_poll(
    poll_id: int,
    db: AsyncSession = Depends(get_db),
    x_admin_api_key: Optional[str] = Header(default=None),
) -> None:
    """Delete a poll and all of its options and votes."""
    from app.core.config import settings

    _require_admin(x_admin_api_key, getattr(settings, "POLLS_ADMIN_API_KEY", None))

    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalars().first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    await db.delete(poll)
    await db.commit()


@router.post("/{poll_id}/vote", response_model=PollResult)
async def cast_vote(
    poll_id: int,
    payload: VoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PollResult:
    """
    Cast a vote on a poll.

    Public endpoint. Basic duplicate protection using poll_id + fingerprint.
    If no fingerprint is provided, the client IP address is used.
    """
    # Load poll and option
    poll_result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = poll_result.scalars().first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    option_result = await db.execute(
        select(PollOption).where(
            PollOption.id == payload.option_id,
            PollOption.poll_id == poll_id,
        )
    )
    option = option_result.scalars().first()
    if not option:
        raise HTTPException(status_code=400, detail="Invalid option for this poll")

    # Use client-provided fingerprint when available, otherwise fall back to IP
    fingerprint = payload.fingerprint or request.client.host

    vote = PollVote(
      poll_id=poll_id,
      option_id=payload.option_id,
      fingerprint=fingerprint,
    )
    db.add(vote)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="You have already voted in this poll from this device.",
        )

    await db.refresh(poll)
    # Return updated results
    return await _load_poll_with_results(poll, db)

