from pydantic import BaseModel, Field
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class SkillGapAnalysis(BaseModel):
    missing_critical_skills: List[str] = Field(..., description="Must-have skills missing from resume")
    missing_good_to_have: List[str] = Field(default_factory=list)
    present_skills: List[str]
    skill_gap_score: float = Field(..., description="Score out of 100 (higher = better match)")
    recommendations: List[str] = Field(..., description="How to close the skill gaps")


class SkillGapAnalyzer:
    """Analyzes skill gaps between Resume and Job Description"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a senior technical recruiter and skills analyst.
            Compare the candidate's skills with the job requirements and identify genuine skill gaps."""),
            
            ("user", """Job Description:
{job_description}

Candidate Skills & Experience:
{resume_skills}

Provide detailed skill gap analysis in JSON format:
{format_instructions}
""")
        ])

        self.output_parser = PydanticOutputParser(pydantic_object=SkillGapAnalysis)

    def analyze(self, resume_schema, job_description: str) -> SkillGapAnalysis:
        # Prepare resume skills context
        resume_context = self._prepare_resume_context(resume_schema)

        chain = self.prompt | self.llm | self.output_parser

        result = chain.invoke({
            "job_description": job_description,
            "resume_skills": resume_context,
            "format_instructions": self.output_parser.get_format_instructions()
        })
        
        return result

    def _prepare_resume_context(self, resume) -> str:
        skills_text = ", ".join(resume.skills) if resume.skills else "No skills listed"
        
        exp_text = ""
        for exp in resume.experiences[:5]:
            exp_text += f"{exp.position} at {exp.company}: {' '.join(exp.achievements[:4])}\n"
        
        return f"Skills: {skills_text}\n\nExperience Highlights:\n{exp_text}"