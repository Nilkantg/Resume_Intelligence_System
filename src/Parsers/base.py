from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Union


class BaseParser(ABC):
    """Base class for all document parsers"""

    @abstractmethod
    def parse(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Parse document and return structured content"""
        pass

    @abstractmethod
    def get_text(self, file_path: Union[str, Path]) -> str:
        """Return raw text only"""
        pass

    @abstractmethod
    def get_markdown(self, file_path: Union[str, Path]) -> str:
        """Return markdown formatted text (best for LLMs)"""
        pass