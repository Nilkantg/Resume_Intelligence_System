project/
├── venv/
├── data/                  # Sample resumes + JDs (gitignore large files)
├── src/
│   ├── __init__.py
│   ├── parsers/           # Raw text extraction
│   │   ├── base.py
│   │   ├── pdf_parser.py
│   │   └── docx_parser.py
│   ├── extractors/        # LLM-based structured extraction
│   │   ├── resume_schema.py   # Pydantic models
│   │   └── llm_extractor.py
│   ├── analyzers/         # Core features
│   │   ├── ats_scorer.py
│   │   ├── skill_gap.py
│   │   ├── matcher.py
│   │   ├── summarizer.py
│   │   ├── improver.py
│   │   ├── keyword_optimizer.py
│   │   └── section_evaluator.py
│   ├── utils/
│   │   ├── prompts.py     # All your system/user prompts
│   │   ├── embeddings.py
│   │   └── report_generator.py
│   └── main.py            # Orchestrator / CLI entry
├── tests/
├── outputs/               # Generated reports, improved resumes
├── requirements.txt
├── .env
└── README.md