import os
from pathlib import Path
from dotenv import load_dotenv

from Parsers import ResumeParser
from Extractors import LLMResumeExtractor

load_dotenv()

def main():
    # Configuration
    resume_path = "data\nilu_Resume.pdf"
    
    if not Path(resume_path).exists():
        print(f"File not found: {resume_path}")
        print("Please create a 'data' folder and add a sample resume.")
        return

    print("🔄 Parsing resume...")
    parser = ResumeParser()
    parsed_data = parser.parse(resume_path)
    
    print(f"✅ Parsed: {parsed_data['file_name']}")
    print(f"   Pages: {parsed_data.get('num_pages', 'N/A')}")
    print(f"   Text length: {len(parsed_data['text'])} characters\n")

    print("🤖 Extracting structured data using LLM...")
    extractor = LLMResumeExtractor(model_name="gpt-4o-mini")  # or gpt-4o for better accuracy
    
    try:
        resume = extractor.extract(resume_path)
        
        print("\n" + "="*60)
        print("✅ EXTRACTION SUCCESSFUL!")
        print("="*60)
        print(f"Name          : {resume.full_name}")
        print(f"Email         : {resume.email}")
        print(f"Skills Count  : {len(resume.skills)}")
        print(f"Experience    : {len(resume.experiences)} jobs")
        print(f"Education     : {len(resume.education)} entries")
        print(f"Projects      : {len(resume.projects)} projects")
        
        # Save structured data
        import json
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        

        with open(output_dir / "structured_resume1.json", "w", encoding="utf-8") as f:
            f.write(resume.model_dump_json(indent=2))
        
        print(f"\n📁 Structured resume saved to outputs/structured_resume.json")
        
    except Exception as e:
        print(f"❌ Extraction error: {e}")


if __name__ == "__main__":
    main()