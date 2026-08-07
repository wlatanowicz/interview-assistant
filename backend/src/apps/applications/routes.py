from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select

from src.apps.applications.api_errors import ApiErrorCode
from src.apps.applications.models import (
    TERMINAL_APPLICATION_STATES,
    ApplicationState,
    JobApplication,
)
from src.apps.users.deps import get_current_user
from src.apps.users.models import User
from src.utils.api_errors import raise_api_error
from src.utils.deps import get_db_session

router = APIRouter(prefix="/api/applications", tags=["applications"])


class JobApplicationPublic(BaseModel):
    id: UUID
    company: str
    position: str
    state: str
    started_on: date
    finished_on: date | None
    ad_link: str | None
    created_at: datetime
    updated_at: datetime


class JobApplicationListResponse(BaseModel):
    applications: list[JobApplicationPublic]


class JobApplicationCreate(BaseModel):
    company: str = Field(max_length=255)
    position: str = Field(max_length=255)
    started_on: date
    state: ApplicationState = ApplicationState.interested
    ad_link: str | None = Field(default=None, max_length=2048)

    @field_validator("company", "position")
    @classmethod
    def non_empty_stripped(cls, v: str) -> str:
        s = v.strip()
        if not s:
            msg = "must not be empty"
            raise ValueError(msg)
        return s

    @field_validator("ad_link")
    @classmethod
    def strip_ad_link(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


def _to_public(application: JobApplication) -> JobApplicationPublic:
    return JobApplicationPublic(
        id=application.id,
        company=application.company,
        position=application.position,
        state=application.state.value,
        started_on=application.started_on,
        finished_on=application.finished_on,
        ad_link=application.ad_link,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.get("", response_model=JobApplicationListResponse)
def list_applications(
    active: bool | None = Query(default=None),
    user: User = Depends(get_current_user),
    session: Session | None = Depends(get_db_session),
) -> JobApplicationListResponse:
    if session is None:
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    statement = (
        select(JobApplication)
        .where(JobApplication.user_id == user.id)
        .order_by(JobApplication.updated_at.desc())
    )
    if active:
        statement = statement.where(JobApplication.finished_on.is_(None))
    applications = list(session.exec(statement).all())
    return JobApplicationListResponse(
        applications=[_to_public(a) for a in applications],
    )


@router.post("", response_model=JobApplicationPublic, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: JobApplicationCreate,
    user: User = Depends(get_current_user),
    session: Session | None = Depends(get_db_session),
) -> JobApplicationPublic:
    if session is None:
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if payload.state in TERMINAL_APPLICATION_STATES:
        raise_api_error(
            ApiErrorCode.invalid_application_state,
            "Terminal states cannot be set when creating an application",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    now = datetime.now(UTC)
    application = JobApplication(
        user_id=user.id,
        company=payload.company,
        position=payload.position,
        started_on=payload.started_on,
        state=payload.state,
        finished_on=None,
        ad_link=payload.ad_link,
        created_at=now,
        updated_at=now,
    )
    session.add(application)
    session.flush()
    session.refresh(application)
    return _to_public(application)
