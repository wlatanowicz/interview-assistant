"""add job applications and drop demo items

Revision ID: b7e4a1c9023f
Revises: 14c67e743eec
Create Date: 2026-07-15 11:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b7e4a1c9023f"
down_revision: Union[str, Sequence[str], None] = "14c67e743eec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sa.Enum(
        "interested",
        "applied",
        "screening",
        "interviewing",
        "assessment",
        "offer",
        "accepted",
        "rejected",
        "withdrawn",
        "ghosted",
        name="applicationstate",
    ).create(op.get_bind())
    op.create_table(
        "job_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column(
            "state",
            postgresql.ENUM(
                "interested",
                "applied",
                "screening",
                "interviewing",
                "assessment",
                "offer",
                "accepted",
                "rejected",
                "withdrawn",
                "ghosted",
                name="applicationstate",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("finished_on", sa.Date(), nullable=True),
        sa.Column("company", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("position", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("ad_link", sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_job_applications_user_id"),
        "job_applications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_job_applications_user_id_state",
        "job_applications",
        ["user_id", "state"],
        unique=False,
    )
    op.drop_index(op.f("ix_items_name"), table_name="items")
    op.drop_table("items")


def downgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_name"), "items", ["name"], unique=False)
    op.drop_index("ix_job_applications_user_id_state", table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_user_id"), table_name="job_applications")
    op.drop_table("job_applications")
    sa.Enum(name="applicationstate").drop(op.get_bind())
