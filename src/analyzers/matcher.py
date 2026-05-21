from typing import Dict

from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity


class ResumeMatcher:
    """Embedding-based semantic matching between resume and job description."""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    def calculate_match_score(self, resume_text: str, jd_text: str) -> Dict[str, float]:
        """Return semantic similarity score."""
        resume_embedding = self.embeddings.embed_query(resume_text)
        jd_embedding = self.embeddings.embed_query(jd_text)

        similarity = cosine_similarity([resume_embedding], [jd_embedding])[0][0]

        return {
            "overall_match_percentage": round(float(similarity) * 100, 2),
            "semantic_similarity": round(float(similarity), 4),
        }

    def section_wise_match(self, resume_schema, job_description: str) -> Dict[str, float]:
        """Calculate the semantic match between the resume and job description."""
        resume_text = self._get_resume_text(resume_schema)
        return self.calculate_match_score(resume_text, job_description)

    def _get_resume_text(self, resume) -> str:
        skills = " ".join(resume.skills)
        experiences = " ".join(
            f"{exp.position} {exp.company} {' '.join(exp.achievements)}"
            for exp in resume.experiences
        )
        projects = " ".join(
            f"{project.name} {project.description or ''} {' '.join(project.technologies)}"
            for project in resume.projects
        )

        return f"{resume.full_name} {resume.summary or ''} {skills} {experiences} {projects}"
