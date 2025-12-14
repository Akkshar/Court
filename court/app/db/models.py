import enum
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class UserRole(str, enum.Enum):
    PLAINTIFF = "PLAINTIFF"
    DEFENDANT = "DEFENDANT"
    JUROR = "JUROR"
    JUDGE = "JUDGE"

class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class VoteValue(str, enum.Enum):
    GUILTY = "GUILTY"
    NOT_GUILTY = "NOT_GUILTY"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)

    submissions: Mapped[list["CaseSubmission"]] = relationship(back_populates="submitted_by")
    votes: Mapped[list["Vote"]] = relationship(back_populates="juror")

class CaseSubmission(Base):
    __tablename__ = "case_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)

    submitted_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    submitted_by_role: Mapped[UserRole] = mapped_column(Enum(UserRole))

    plaintiff_name: Mapped[str] = mapped_column(String(120), index=True)
    defendant_name: Mapped[str] = mapped_column(String(120), index=True)

    argument_text: Mapped[str] = mapped_column(Text)
    evidence_text: Mapped[str] = mapped_column(Text)

    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)
    judge_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    submitted_by: Mapped["User"] = relationship(back_populates="submissions")

class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("case_id", "juror_user_id", name="uq_vote_once_per_case"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)

    juror_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vote: Mapped[VoteValue] = mapped_column(Enum(VoteValue))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    juror: Mapped["User"] = relationship(back_populates="votes")