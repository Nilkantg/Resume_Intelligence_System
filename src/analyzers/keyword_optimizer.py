from typing import Dict, List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class KeywordOptimization(BaseModel):
    recommended_keywords: List[str]
    keywords_to_add: List[str]
    placement_suggestions: List[str]
    optimized_sections: Dict[str, str]
    ats_optimization_score: float


class KeywordOptimizer:
    """Optimizes resume keywords for ATS and job description matching."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an ATS optimization expert.
Suggest natural keyword integration without keyword stuffing.""",
                ),
                (
                    "user",
                    """Job Description:
{job_description}

Current Resume Skills & Content:
{resume_data}

Provide keyword optimization strategy in this JSON format:
{format_instructions}
""",
                ),
            ]
        )

        self.output_parser = PydanticOutputParser(pydantic_object=KeywordOptimization)

    def optimize(self, resume_schema, job_description: str) -> KeywordOptimization:
        resume_context = self._prepare_context(resume_schema)
        chain = self.prompt | self.llm | self.output_parser

        return chain.invoke(
            {
                "job_description": job_description,
                "resume_data": resume_context,
                "format_instructions": self.output_parser.get_format_instructions(),
            }
        )

    def _prepare_context(self, resume) -> str:
        experience_highlights = " ".join(
            f"{exp.position} {exp.company} {' '.join(exp.achievements[:3])}"
            for exp in resume.experiences
        )

        project_highlights = " ".join(
            f"{project.name} {project.description or ''} {' '.join(project.technologies)}"
            for project in resume.projects
        )

        return (
            f"Skills: {', '.join(resume.skills)}\n\n"
            f"Experience Highlights: {experience_highlights}\n\n"
            f"Project Highlights: {project_highlights}"
        )
