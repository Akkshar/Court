from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.db.models import Vote, VoteValue, User, UserRole
from app.db.session import get_db
from app.schemas import VoteRequest, VoteResultOut

router = APIRouter(prefix="/jury", tags=["jury"])

@router.post("/vote/{case_id}", status_code=201)
def vote(case_id: str, payload: VoteRequest, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.JUROR))):
    v = Vote(case_id=case_id, juror_user_id=user.id, vote=payload.vote)
    db.add(v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="You already voted for this case")
    return {"message": "Vote recorded"}

@router.get("/results/{case_id}", response_model=VoteResultOut)
def results(case_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in (UserRole.JUROR, UserRole.JUDGE):
        raise HTTPException(status_code=403, detail="Forbidden")

    guilty = db.scalar(select(func.count()).select_from(Vote).where(Vote.case_id == case_id, Vote.vote == VoteValue.GUILTY)) or 0
    not_guilty = db.scalar(select(func.count()).select_from(Vote).where(Vote.case_id == case_id, Vote.vote == VoteValue.NOT_GUILTY)) or 0
    total = guilty + not_guilty
    return VoteResultOut(case_id=case_id, guilty=guilty, not_guilty=not_guilty, total=total)