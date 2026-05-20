from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class Experience(BaseModel):
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job title / Position")
    location: Optional[str] = Field(None, description="Location of the job")
    start_date: Optional[str] = Field(None, description="Start date (Month Year or Year)")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    duration: Optional[str] = None
    achievements: List[str] = Field(default_factory=list, description="Bullet points / Key achievements")


class Education(BaseModel):
    degree: str = Field(..., description="Degree name")
    institution: str = Field(..., description="University / College name")
    location: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[float] = None


class Project(BaseModel):
    name: str = Field(..., description="Project name")
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None


class ResumeSchema(BaseModel):
    """Complete structured schema for a resume"""
    
    full_name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    summary: Optional[str] = Field(None, description="Professional summary")
    
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    
    experiences: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    
    certifications: List[str] = Field(default_factory=list)
    
    # Metadata
    total_years_experience: Optional[float] = None
    raw_text_length: Optional[int] = None
    extraction_confidence: Optional[float] = None