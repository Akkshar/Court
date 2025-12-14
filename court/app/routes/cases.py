from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.db.models import CaseSubmission, SubmissionStatus, User, UserRole
from app.db.session import get_db
from app.schemas import (
    CaseSubmitRequest,
    SubmissionOut,
    SubmissionEditRequest,
    SubmissionDecisionRequest,
)

router = APIRouter(prefix="/case", tags=["cases"])

def _submission_to_out(s: CaseSubmission) -> SubmissionOut:
    return SubmissionOut(
        id=s.id,
        case_id=s.case_id,
        plaintiff_name=s.plaintiff_name,
        defendant_name=s.defendant_name,
        submitted_by_role=s.submitted_by_role,
        argument_text=s.argument_text,
        evidence_text=s.evidence_text,
        status=s.status,
        judge_notes=s.judge_notes,
    )

@router.post("/submit", response_model=SubmissionOut, status_code=201)
def submit_case(
    payload: CaseSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.PLAINTIFF, UserRole.DEFENDANT)),
):
    submission = CaseSubmission(
        case_id=payload.case_id,
        submitted_by_user_id=user.id,
        submitted_by_role=user.role,
        plaintiff_name=payload.plaintiff_name,
        defendant_name=payload.defendant_name,
        argument_text=payload.argument_text,
        evidence_text=payload.evidence_text,
        status=SubmissionStatus.PENDING,  # judge approval mandatory
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return _submission_to_out(submission)

@router.get("/all", response_model=list[SubmissionOut])
def get_all(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Jurors see only approved submissions.
    if user.role == UserRole.JUROR:
        rows = db.scalars(select(CaseSubmission).where(CaseSubmission.status == SubmissionStatus.APPROVED)).all()
        return [_submission_to_out(r) for r in rows]

    # Plaintiffs/Defendants: see their own + approved (keeps privacy while meeting "all roles can view")
    if user.role in (UserRole.PLAINTIFF, UserRole.DEFENDANT):
        rows = db.scalars(
            select(CaseSubmission).where(
                or_(
                    CaseSubmission.submitted_by_user_id == user.id,
                    CaseSubmission.status == SubmissionStatus.APPROVED
                )
            )
        ).all()
        return [_submission_to_out(r) for r in rows]

    # Judge: everything
    rows = db.scalars(select(CaseSubmission)).all()
    return [_submission_to_out(r) for r in rows]

@router.get("/by-name/{name}", response_model=list[SubmissionOut])
def by_name(
    name: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.JUROR)),
):
    # Jurors can only filter within APPROVED submissions
    n = name.strip()
    rows = db.scalars(
        select(CaseSubmission).where(
            CaseSubmission.status == SubmissionStatus.APPROVED,
        ).where(
            or_(
                CaseSubmission.plaintiff_name.ilike(f"%{n}%"),
                CaseSubmission.defendant_name.ilike(f"%{n}%"),
            )
        )
    ).all()
    return [_submission_to_out(r) for r in rows]

@router.patch("/edit/{submission_id}", response_model=SubmissionOut)
def edit_submission(
    submission_id: int,
    payload: SubmissionEditRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.JUDGE)),
):
    s = db.get(CaseSubmission, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(s, field, value)

    db.commit()
    db.refresh(s)
    return _submission_to_out(s)

@router.delete("/delete/{submission_id}", status_code=204)
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.JUDGE)),
):
    s = db.get(CaseSubmission, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    db.delete(s)
    db.commit()
    return None

@router.patch("/approve/{submission_id}", response_model=SubmissionOut)
def approve_submission(
    submission_id: int,
    payload: SubmissionDecisionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.JUDGE)),
):
    s = db.get(CaseSubmission, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    s.status = SubmissionStatus.APPROVED
    if payload.judge_notes is not None:
        s.judge_notes = payload.judge_notes
    db.commit()
    db.refresh(s)
    return _submission_to_out(s)

@router.patch("/reject/{submission_id}", response_model=SubmissionOut)
def reject_submission(
    submission_id: int,
    payload: SubmissionDecisionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.JUDGE)),
):
    s = db.get(CaseSubmission, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    s.status = SubmissionStatus.REJECTED
    if payload.judge_notes is not None:
        s.judge_notes = payload.judge_notes
    db.commit()
    db.refresh(s)
    return _submission_to_out(s)