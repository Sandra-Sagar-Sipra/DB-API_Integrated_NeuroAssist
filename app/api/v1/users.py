from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.db import get_session
from app.models.base import User, PatientProfile, UserRole
from app.api.deps import get_current_user
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class PatientProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    medical_history: Optional[str] = None

@router.put("/me/profile", response_model=PatientProfile)
def update_my_profile(
    profile_in: PatientProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update the current logged-in user's profile.
    Currently supports PATIENT role.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(status_code=400, detail="Profile update currently only supported for Patients")
        
    # User relationship lazy loading might need explicit query if not loaded
    # But usually we can query the profile directly by user_id
    profile = session.exec(select(PatientProfile).where(PatientProfile.user_id == current_user.id)).first()
    
    if not profile:
        # Should have been created at signup, but if missing, create one?
        # Better to error out or create. Let's create if missing for robustness.
        profile = PatientProfile(user_id=current_user.id, first_name="", last_name="")
        session.add(profile)
    
    profile_data = profile_in.model_dump(exclude_unset=True)
    for key, value in profile_data.items():
        setattr(profile, key, value)
        
    profile.updated_at = datetime.utcnow()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

@router.get("/me/profile", response_model=PatientProfile)
def get_my_profile(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.PATIENT:
         raise HTTPException(status_code=400, detail="Endpoint currently for Patients only")
         
    profile = session.exec(select(PatientProfile).where(PatientProfile.user_id == current_user.id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
