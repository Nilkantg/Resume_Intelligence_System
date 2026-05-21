from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class ImprovementSuggestion(BaseModel):
    section: str
    issue: str
    suggestion: str
    rewritten_example: str | None = None
    impact: str


class ResumeImproverOutput(BaseModel):
    overall_score: float
    suggestions: List[ImprovementSuggestion]
    rewritten_summary: str | None = None
    key_improvements: List[str]


class ResumeImprover:
    """Provides detailed resume improvement suggestions."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.3)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert resume improvement coach.
Be honest, constructive, and specific. Focus on quantifiable achievements and strong action verbs.""",
                ),
                (
                    "user",
                    """Resume:
{resume_data}

Analyze and suggest improvements. Return JSON:
{format_instructions}
""",
                ),
            ]
        )

        self.output_parser = PydanticOutputParser(pydantic_object=ResumeImproverOutput)

    def improve(self, resume_schema) -> ResumeImproverOutput:
        resume_text = self._detailed_resume_text(resume_schema)
        chain = self.prompt | self.llm | self.output_parser

        return chain.invoke(
            {
                "resume_data": resume_text,
                "format_instructions": self.output_parser.get_format_instructions(),
            }
        )

    def _detailed_resume_text(self, resume) -> str:
        text = f"Name: {resume.full_name}\n\n"
        if resume.summary:
            text += f"Summary:\n{resume.summary}\n\n"

        text += "Skills:\n" + ", ".join(resume.skills) + "\n\n"

        text += "Experience:\n"
        for exp in resume.experiences:
            text += f"- {exp.position} | {exp.company} | {exp.start_date} - {exp.end_date}\n"
            for ach in exp.achievements:
                text += f"  - {ach}\n"

        return text
