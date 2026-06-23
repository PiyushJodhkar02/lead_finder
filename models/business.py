from pydantic import BaseModel, Field
from typing import Optional

class Business(BaseModel):
    company_name: str
    industry: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    company_size: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fit_score: Optional[int] = None
    fit_reason: Optional[str] = None
