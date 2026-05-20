import pymupdf
import pymupdf4llm
from pathlib import Path
from typing import Dict, Any, Union
from .base import BaseParser


class PDFParser(BaseParser):
    """PDF Parser using PyMuPDF - Very reliable and fast"""

    def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = pymupdf.open(file_path)
        
        result = {
            "file_name": file_path.name,
            "file_type": "pdf",
            "num_pages": len(doc),
            "text": "",
            "markdown": "",
            "pages": [],
            "metadata": doc.metadata
        }

        # Extract text page by page
        full_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            result["pages"].append({
                "page_number": page_num + 1,
                "text": text.strip(),
                "word_count": len(text.split())
            })
            full_text.append(text)

        result["text"] = "\n\n".join(full_text).strip()
        
        # Get clean markdown (excellent for LLMs)
        try:
            result["markdown"] = pymupdf4llm.to_markdown(doc)
        except Exception:
            result["markdown"] = result["text"]  # fallback

        doc.close()
        return result

    def get_text(self, file_path: Union[str, Path]) -> str:
        return self.parse(file_path)["text"]

    def get_markdown(self, file_path: Union[str, Path]) -> str:
        return self.parse(file_path)["markdown"]
