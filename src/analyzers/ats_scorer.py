from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json


class ATSScore(BaseModel):
    overall_score: float = Field(..., description="Overall ATS score out of 100")
    keyword_match_score: float
    skills_match_score: float
    experience_match_score: float
    format_score: float
    missing_keywords: List[str]
    strong_points: List[str]
    weak_points: List[str]
    recommendations: List[str]


class ATSScorer:
    """ATS Score + Job Description Matching"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        
        self.ats_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert ATS (Applicant Tracking System) specialist and senior recruiter.
            Analyze the resume against the job description and give a highly accurate ATS compatibility score."""),
            
            ("user", """Job Description:
{job_description}

Resume:
{resume_data}

Analyze and return a detailed JSON with the following structure:
{format_instructions}
""")
        ])

    def score(self, resume_schema, job_description: str) -> ATSScore:
        """Score resume against JD"""
        
        # Convert resume to readable text for LLM
        resume_text = self._resume_to_text(resume_schema)

        parser = PydanticOutputParser(pydantic_object=ATSScore)  # Need to import

        chain = self.ats_prompt | self.llm | parser   # PydanticOutputParser

        response = chain.invoke({
            "job_description": job_description,
            "resume_data": resume_text,
            "format_instructions": parser.get_format_instructions()
        })

        return response

    def _resume_to_text(self, resume) -> str:
        """Convert structured resume to clean text for analysis"""
        text = f"Name: {resume.full_name}\n\n"
        
        if resume.summary:
            text += f"Summary:\n{resume.summary}\n\n"
        
        text += "Skills:\n" + ", ".join(resume.skills) + "\n\n"
        
        text += "Experience:\n"
        for exp in resume.experiences:
            text += f"- {exp.position} at {exp.company} ({exp.start_date} - {exp.end_date})\n"
            for achievement in exp.achievements[:6]:   # limit
                text += f"  • {achievement}\n"
            text += "\n"
        
        text += "Education:\n"
        for edu in resume.education:
            text += f"- {edu.degree} from {edu.institution}\n"
        
        return text


# Temporary fix - we'll improve imports later
from langchain_core.output_parsers import PydanticOutputParser