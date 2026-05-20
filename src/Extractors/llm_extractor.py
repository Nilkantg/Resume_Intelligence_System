import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, AuthenticationError

from .resume_schema import ResumeSchema
from ..Parsers import ResumeParser

load_dotenv()

class LLMResumeExtractor:
    """Extracts structured information from resume using LLM"""

    PLACEHOLDER_SNIPPETS: ClassVar[tuple[str, ...]] = (
        "your_actual_api_key_here",
        "your_openai_api_key",
        "replace_me",
        "paste_key_here",
        "api_key_here",
    )

    @staticmethod
    def validate_api_key(api_key: str | None = None) -> tuple[bool, str | None]:
        api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()

        if not api_key:
            return False, "OPENAI_API_KEY is not set. Add it to your .env file to enable LLM extraction."

        lowered = api_key.lower()
        if any(snippet in lowered for snippet in LLMResumeExtractor.PLACEHOLDER_SNIPPETS):
            return False, "OPENAI_API_KEY still contains placeholder text. Replace it with your real OpenAI API key."

        if " " in api_key:
            return False, "OPENAI_API_KEY contains spaces. Paste only the raw key value into the .env file."

        if not api_key.startswith("sk-"):
            return False, "OPENAI_API_KEY format looks unusual. For the OpenAI API it should normally start with 'sk-'."

        return True, None

    def __init__(self, model_name: str = "gpt-4o-mini"):
        is_valid, validation_message = self.validate_api_key()
        if not is_valid:
            raise ValueError(validation_message)

        self.model_name = model_name
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.0,          # Low temperature for factual extraction
            max_tokens=4000
        )
        self.parser = ResumeParser()
        
        self.output_parser = PydanticOutputParser(pydantic_object=ResumeSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume parser. Extract information accurately and professionally.
            Return the data in strict JSON format according to the given schema.
            If information is missing, use null or empty list. Do not hallucinate."""),
            
            ("user", """Here is the resume content:

{resume_content}

Extract all information following this format:

{format_instructions}
""")
        ])    

    def test_openai_connection(self) -> None:
        """Verify that the OpenAI API is reachable before running extraction."""
        try:
            self.llm.invoke("Reply with OK.")
        except AuthenticationError as e:
            raise ValueError(
                "OpenAI rejected the API key. Double-check OPENAI_API_KEY in your .env file and confirm the key is active."
            ) from e
        except APIConnectionError as e:
            raise ConnectionError(
                "Could not reach the OpenAI API. Check your internet connection and try again."
            ) from e
        except Exception as e:
            print(f"Connection test failed: {e}")
            raise

    def extract(self, file_path: str | Path) -> ResumeSchema:
        """Parse file and extract structured resume"""
        # Step 1: Get clean markdown (best for LLMs)
        raw_data = self.parser.parse(file_path)
        markdown_text = raw_data["markdown"]

        # Step 2: Create prompt
        chain = self.prompt | self.llm | self.output_parser
        
        try:
            structured_resume: ResumeSchema = chain.invoke({
                "resume_content": markdown_text,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            
            # Add metadata
            structured_resume.raw_text_length = len(raw_data["text"])
            structured_resume.extraction_confidence = 0.85  # Placeholder
            
            # Optional: Calculate total experience (can be improved later)
            return structured_resume

        except AuthenticationError as e:
            raise ValueError(
                "OpenAI rejected the API key. Double-check OPENAI_API_KEY in your .env file and confirm the key is active."
            ) from e
        except APIConnectionError as e:
            raise ConnectionError(
                "Could not reach the OpenAI API. Check your internet connection and try again."
            ) from e
        except Exception as e:
            print(f"Extraction failed: {e}")
            raise

    def extract_from_text(self, text: str) -> ResumeSchema:
        """Direct extraction from text (useful for testing)"""
        chain = self.prompt | self.llm | self.output_parser
        structured_resume = chain.invoke({
            "resume_content": text,
            "format_instructions": self.output_parser.get_format_instructions()
        })
        
        return structured_resume
