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

# Parametrize model
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,     # 0.0 = deterministic, 1.0+ = creative/random
    max_tokens=1000,     # max tokens in the response
    top_p=0.9,           # nucleus sampling (alternative to temperature)
    frequency_penalty=0, # penalize repeating same words (-2 to 2)
    presence_penalty=0,  # penalize repeating same topics (-2 to 2)
    timeout=30,          # seconds before request times out
    max_retries=2,       # retry on failure
    n=1,                 # number of completions to generate
)

