import json
from pathlib import Path

from dotenv import load_dotenv

from src.Extractors import LLMResumeExtractor
from src.Parsers import ResumeParser
from src.analyzers import ATSScorer, SectionEvaluator, SkillGapAnalyzer

load_dotenv()


def run_analysis_step(label, callback):
    print(f"Running {label}...")
    try:
        result = callback()
        return result.model_dump(mode="json")
    except Exception as e:
        return {"error": str(e)}


def main():
    # Configuration
    resume_path = Path("data") / "nilu_Resume.pdf"
    job_description_path = Path("data") / "jd_1"

    if not resume_path.exists():
        print(f"File not found: {resume_path}")
        print("Please create a 'data' folder and add a sample resume.")
        return

    if not job_description_path.exists():
        print(f"File not found: {job_description_path}")
        print("Please add a job description file before running analysis.")
        return

    job_description = job_description_path.read_text(encoding="utf-8")

    print("Parsing resume...")
    parser = ResumeParser()
    parsed_data = parser.parse(resume_path)

    print(f"Parsed: {parsed_data['file_name']}")
    print(f"   Pages: {parsed_data.get('num_pages', 'N/A')}")
    print(f"   Text length: {len(parsed_data['text'])} characters\n")

    print("Extracting structured data using LLM...")
    extractor = LLMResumeExtractor(model_name="gpt-4o-mini")

    try:
        resume = extractor.extract(resume_path)

        print("\n" + "=" * 60)
        print("EXTRACTION SUCCESSFUL!")
        print("=" * 60)
        print(f"Name          : {resume.full_name}")
        print(f"Email         : {resume.email}")
        print(f"Skills Count  : {len(resume.skills)}")
        print(f"Experience    : {len(resume.experiences)} jobs")
        print(f"Education     : {len(resume.education)} entries")
        print(f"Projects      : {len(resume.projects)} projects")

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        structured_resume_path = output_dir / "structured_resume1.json"
        analysis_report_path = output_dir / "resume_analysis_report.json"

        with structured_resume_path.open("w", encoding="utf-8") as f:
            f.write(resume.model_dump_json(indent=2))

        print("\nAnalyzing resume against job description...")
        ats_score = run_analysis_step(
            "ATS score",
            lambda: ATSScorer(model_name="gpt-4o-mini").score(resume, job_description),
        )
        section_evaluation = run_analysis_step(
            "section evaluation",
            lambda: SectionEvaluator(model_name="gpt-4o-mini").evaluate(resume),
        )
        skill_gap_analysis = run_analysis_step(
            "skill gap analysis",
            lambda: SkillGapAnalyzer(model_name="gpt-4o-mini").analyze(
                resume,
                job_description,
            ),
        )

        if "overall_score" in ats_score:
            print(f"ATS Score     : {ats_score['overall_score']}/100")
        if "overall_section_score" in section_evaluation:
            print(f"Section Score : {section_evaluation['overall_section_score']}/100")
        if "skill_gap_score" in skill_gap_analysis:
            print(f"Skill Match   : {skill_gap_analysis['skill_gap_score']}/100")

        analysis_report = {
            "resume_file": str(resume_path),
            "job_description_file": str(job_description_path),
            "job_description": job_description,
            "structured_resume": resume.model_dump(mode="json"),
            "ats_score": ats_score,
            "section_evaluation": section_evaluation,
            "skill_gap_analysis": skill_gap_analysis,
        }

        with analysis_report_path.open("w", encoding="utf-8") as f:
            json.dump(analysis_report, f, indent=2, ensure_ascii=False)

        print(f"\nStructured resume saved to {structured_resume_path}")
        print(f"Analysis report saved to {analysis_report_path}")

    except Exception as e:
        print(f"Processing error: {e}")


if __name__ == "__main__":
    main()
