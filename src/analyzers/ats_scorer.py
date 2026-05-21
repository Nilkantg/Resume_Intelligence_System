from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


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
    """ATS score and job description matching."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        self.output_parser = PydanticOutputParser(pydantic_object=ATSScore)

        self.ats_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert ATS (Applicant Tracking System) specialist and senior recruiter.
Analyze the resume against the job description and give a highly accurate ATS compatibility score.""",
                ),
                (
                    "user",
                    """Job Description:
{job_description}

Resume:
{resume_data}

Analyze and return a detailed JSON with the following structure:
{format_instructions}
""",
                ),
            ]
        )

    def score(self, resume_schema, job_description: str) -> ATSScore:
        """Score resume against a job description."""
        resume_text = self._resume_to_text(resume_schema)
        chain = self.ats_prompt | self.llm | self.output_parser

        return chain.invoke(
            {
                "job_description": job_description,
                "resume_data": resume_text,
                "format_instructions": self.output_parser.get_format_instructions(),
            }
        )

    def _resume_to_text(self, resume) -> str:
        """Convert structured resume data to clean text for analysis."""
        text = f"Name: {resume.full_name}\n\n"

        if resume.summary:
            text += f"Summary:\n{resume.summary}\n\n"

        text += "Skills:\n" + ", ".join(resume.skills) + "\n\n"

        text += "Experience:\n"
        for exp in resume.experiences:
            text += f"- {exp.position} at {exp.company} ({exp.start_date} - {exp.end_date})\n"
            for achievement in exp.achievements[:6]:
                text += f"  - {achievement}\n"
            text += "\n"

        text += "Education:\n"
        for edu in resume.education:
            text += f"- {edu.degree} from {edu.institution}\n"

        return text
