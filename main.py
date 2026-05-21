from pathlib import Path

from dotenv import load_dotenv

from src.Extractors import LLMResumeExtractor
from src.Parsers import ResumeParser

load_dotenv()


def main():
    # Configuration
    resume_path = Path("data") / "nilu_Resume.pdf"

    if not resume_path.exists():
        print(f"File not found: {resume_path}")
        print("Please create a 'data' folder and add a sample resume.")
        return

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
        output_path = output_dir / "structured_resume1.json"

        with output_path.open("w", encoding="utf-8") as f:
            f.write(resume.model_dump_json(indent=2))

        print(f"\nStructured resume saved to {output_path}")

    except Exception as e:
        print(f"Extraction error: {e}")


if __name__ == "__main__":
    main()
