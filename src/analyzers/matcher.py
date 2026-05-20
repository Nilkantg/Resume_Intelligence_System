from typing import Dict, List, Tuple
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class ResumeMatcher:
    """Embedding-based semantic matching between Resume and Job Description"""
    
    def __init__(self):
        # Using a good lightweight embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def calculate_match_score(self, resume_text: str, jd_text: str) -> Dict[str, float]:
        """Return semantic similarity score"""
        resume_emb = self.embeddings.embed_query(resume_text)
        jd_emb = self.embeddings.embed_query(jd_text)
        
        similarity = cosine_similarity([resume_emb], [jd_emb])[0][0]
        
        return {
            "overall_match_percentage": round(similarity * 100, 2),
            "semantic_similarity": round(float(similarity), 4)
        }

    def section_wise_match(self, resume_schema, job_description: str) -> Dict:
        """Section-wise matching (can be expanded)"""
        resume_text = self._get_resume_text(resume_schema)
        
        return self.calculate_match_score(resume_text, job_description)

    def _get_resume_text(self, resume) -> str:
        skills = " ".join(resume.skills)
        experiences = " ".join([f"{e.position} {e.company} {' '.join(e.achievements)}" 
                              for e in resume.experiences])
        return f"{resume.full_name} {resume.summary or ''} {skills} {experiences}"