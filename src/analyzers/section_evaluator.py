from pydantic import BaseModel, Field
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class SectionScore(BaseModel):
    section_name: str
    score: float = Field(..., description="Score out of 100")
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class SectionEvaluation(BaseModel):
    overall_section_score: float
    sections: List[SectionScore]
    top_improvement_areas: List[str]


class SectionEvaluator:
    """Evaluates quality of each section in the resume"""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume coach and career advisor.
            Critically evaluate each section of the resume for quality, impact, and effectiveness."""),
            
            ("user", """Resume Content:
{resume_data}

Evaluate each major section and provide detailed feedback in this exact JSON format:
{format_instructions}
""")
        ])

        self.output_parser = PydanticOutputParser(pydantic_object=SectionEvaluation)

    def evaluate(self, resume_schema) -> SectionEvaluation:
        resume_text = self._resume_to_detailed_text(resume_schema)

        chain = self.prompt | self.llm | self.output_parser

        result: SectionEvaluation = chain.invoke({
            "resume_data": resume_text,
            "format_instructions": self.output_parser.get_format_instructions()
        })
        
        return result

    def _resume_to_detailed_text(self, resume) -> str:
        text = f"Candidate: {resume.full_name}\n\n"
        
        if resume.summary:
            text += f"Summary:\n{resume.summary}\n\n"
        
        text += f"Skills ({len(resume.skills)}):\n{', '.join(resume.skills[:30])}\n\n"
        
        text += "Experience:\n"
        for i, exp in enumerate(resume.experiences):
            text += f"{i+1}. {exp.position} at {exp.company}\n"
            for ach in exp.achievements[:5]:
                text += f"   • {ach}\n"
            text += "\n"
        
        return text