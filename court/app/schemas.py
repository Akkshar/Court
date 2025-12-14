from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from app.db.models import UserRole, SubmissionStatus, VoteValue

class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole

class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

class CaseSubmitRequest(BaseModel):
    case_id: str = Field(min_length=3, max_length=64)
    plaintiff_name: str = Field(min_length=1, max_length=120)
    defendant_name: str = Field(min_length=1, max_length=120)
    argument_text: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)

class SubmissionOut(BaseModel):
    id: int
    case_id: str
    plaintiff_name: str
    defendant_name: str
    submitted_by_role: UserRole
    argument_text: str
    evidence_text: str
    status: SubmissionStatus
    judge_notes: Optional[str] = None

class SubmissionEditRequest(BaseModel):
    plaintiff_name: Optional[str] = None
    defendant_name: Optional[str] = None
    argument_text: Optional[str] = None
    evidence_text: Optional[str] = None
    judge_notes: Optional[str] = None

class SubmissionDecisionRequest(BaseModel):
    judge_notes: Optional[str] = None

class VoteRequest(BaseModel):
    vote: VoteValue

class VoteResultOut(BaseModel):
    case_id: str
    guilty: int
    not_guilty: int
    total: int