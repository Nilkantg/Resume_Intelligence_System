from pathlib import Path
from typing import Dict, Any, Union
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser


class ResumeParser:
    """Main parser that handles multiple file types"""

    def __init__(self):
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()

    def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Auto detect and parse resume"""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self.pdf_parser.parse(file_path)
        elif suffix in [".docx", ".doc"]:
            return self.docx_parser.parse(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: .pdf, .docx")

    def get_text(self, file_path: Union[str, Path]) -> str:
        return self.parse(file_path)["text"]

    def get_markdown(self, file_path: Union[str, Path]) -> str:
        return self.parse(file_path)["markdown"]


# For easy import
__all__ = ["ResumeParser", "PDFParser", "DOCXParser"]