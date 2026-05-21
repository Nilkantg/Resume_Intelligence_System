from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class ProfessionalSummary(BaseModel):
    summary: str = Field(..., description="Professional summary (3-5 sentences)")
    key_value_proposition: str = Field(..., description="One-line unique value proposition")
    keywords_to_highlight: List[str]


class ResumeSummarizer:
    """Generates a high-impact professional summary."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.3)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a senior career coach and executive resume writer.
Write powerful, achievement-oriented professional summaries.""",
                ),
                (
                    "user",
                    """Resume Information:
{resume_data}

Write a compelling professional summary.
Return in this exact JSON format:
{format_instructions}
""",
                ),
            ]
        )

        self.output_parser = PydanticOutputParser(pydantic_object=ProfessionalSummary)

    def generate_summary(self, resume_schema) -> ProfessionalSummary:
        resume_text = self._resume_to_context(resume_schema)
        chain = self.prompt | self.llm | self.output_parser

        return chain.invoke(
            {
                "resume_data": resume_text,
                "format_instructions": self.output_parser.get_format_instructions(),
            }
        )

    def _resume_to_context(self, resume) -> str:
        context = f"Name: {resume.full_name}\n"
        if resume.summary:
            context += f"Current Summary: {resume.summary}\n\n"

        context += f"Skills: {', '.join(resume.skills[:25])}\n\n"

        context += "Experience:\n"
        for exp in resume.experiences[:4]:
            context += f"- {exp.position} at {exp.company}\n"
            for ach in exp.achievements[:3]:
                context += f"  - {ach}\n"

        return context
