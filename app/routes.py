from flask import Blueprint, current_app, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

from src.Parsers import ResumeParser
from src.Extractors import LLMResumeExtractor
from src.analyzers import (
    ATSScorer, ResumeMatcher, SkillGapAnalyzer,
    SectionEvaluator, ResumeSummarizer,
    ResumeImprover, KeywordOptimizer
)
from src.utils.report_generator import ReportGenerator

bp = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def list_report_files():
    output_folder = Path(current_app.config["OUTPUT_FOLDER"])
    if not output_folder.exists():
        return []

    return sorted(
        file.name
        for file in output_folder.iterdir()
        if file.is_file()
    )


def save_upload(file):
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(exist_ok=True)
    file_path = upload_folder / unique_filename
    file.save(file_path)
    return file_path


def cleanup_file(file_path):
    if file_path and file_path.exists():
        file_path.unlink()

@bp.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "AI Resume Intelligence API is running",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "extract_only": "/extract-only",
            "reports": "/reports",
            "download_report": "/reports/<filename>",
        },
    })


@bp.route('/favicon.ico', methods=['GET'])
def favicon():
    return "", 204


@bp.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "AI Resume Intelligence API is running"})

@bp.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    job_description = request.form.get('job_description', '')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files allowed"}), 400

    file_path = save_upload(file)

    try:
        # Core Pipeline
        extractor = LLMResumeExtractor(model_name="gpt-4o-mini")
        resume = extractor.extract(file_path)

        # Run Analyzers
        ats_result = ATSScorer().score(resume, job_description)
        match_result = ResumeMatcher().section_wise_match(resume, job_description)
        skill_gap = SkillGapAnalyzer().analyze(resume, job_description)
        section_eval = SectionEvaluator().evaluate(resume)
        summary = ResumeSummarizer().generate_summary(resume)
        improvements = ResumeImprover().improve(resume)
        keywords_opt = KeywordOptimizer().optimize(resume, job_description)

        # Generate Report
        report_gen = ReportGenerator(current_app.config["OUTPUT_FOLDER"])
        final_report = report_gen.generate_full_report(
            resume, ats_result, match_result, skill_gap,
            section_eval, summary, improvements, keywords_opt, job_description
        )

        return jsonify({
            "success": True,
            "candidate_name": resume.full_name,
            "overall_scores": final_report["overall_scores"],
            "professional_summary": final_report["professional_summary"],
            "missing_skills": final_report["missing_critical_skills"],
            "top_improvements": final_report["top_improvements"],
            "report_id": str(uuid.uuid4())
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_file(file_path)


@bp.route('/reports', methods=['GET'])
def list_reports():
    """List generated reports that can be downloaded."""
    reports = list_report_files()
    return jsonify({
        "reports": reports,
        "download_urls": [f"/reports/{filename}" for filename in reports],
    })


@bp.route('/reports/<path:filename>', methods=['GET'])
def get_report(filename):
    """Download generated reports"""
    output_folder = Path(current_app.config["OUTPUT_FOLDER"])
    if not (output_folder / filename).is_file():
        return jsonify({
            "error": f"Report not found: {filename}",
            "available_reports": list_report_files(),
        }), 404

    return send_from_directory(current_app.config["OUTPUT_FOLDER"], filename)


@bp.route('/extract-only', methods=['POST'])
def extract_only():
    """Only parse and extract structured data (lighter endpoint)"""
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files allowed"}), 400

    file_path = save_upload(file)

    try:
        parser = ResumeParser()
        parsed_data = parser.parse(file_path)
        extractor = LLMResumeExtractor(model_name="gpt-4o-mini")
        resume = extractor.extract(file_path)

        return jsonify({
            "success": True,
            "parsed_file": {
                "file_name": parsed_data.get("file_name"),
                "num_pages": parsed_data.get("num_pages"),
                "text_length": len(parsed_data.get("text", "")),
            },
            "resume": resume.model_dump(mode="json"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cleanup_file(file_path)
