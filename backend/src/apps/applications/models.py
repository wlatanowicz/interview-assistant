from __future__ import annotations

import enum
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Index
from sqlmodel import Column, Field, SQLModel

from src.utils.db import to_sql_enum


class ApplicationState(enum.StrEnum):
    interested = "interested"
    applied = "applied"
    screening = "screening"
    interviewing = "interviewing"
    assessment = "assessment"
    offer = "offer"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"
    ghosted = "ghosted"


TERMINAL_APPLICATION_STATES: frozenset[ApplicationState] = frozenset(
    {
        ApplicationState.accepted,
        ApplicationState.rejected,
        ApplicationState.withdrawn,
        ApplicationState.ghosted,
    }
)


class JobApplication(SQLModel, table=True):
    __tablename__ = "job_applications"
    __table_args__ = (Index("ix_job_applications_user_id_state", "user_id", "state"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    started_on: date = Field(sa_column=Column(Date, nullable=False))
    state: ApplicationState = Field(
        sa_column=Column(
            to_sql_enum(ApplicationState, name="applicationstate"),
            nullable=False,
        ),
    )
    finished_on: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    company: str = Field(max_length=255)
    position: str = Field(max_length=255)
    ad_link: str | None = Field(default=None, max_length=2048)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
