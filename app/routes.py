import hashlib
import json
from datetime import datetime
from flask import Blueprint, Response, current_app, request, jsonify, render_template, send_from_directory
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
CACHE_INDEX_FILENAME = "cache_index.json"
OUTPUT_FORMAT_ALIASES = {
    "json": "json",
    "markdown": "markdown",
    "md": "markdown",
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def list_report_files():
    output_folder = Path(current_app.config["OUTPUT_FOLDER"])
    if not output_folder.exists():
        return []

    return sorted(
        file.name
        for file in output_folder.iterdir()
        if file.is_file() and file.name != CACHE_INDEX_FILENAME
    )


def get_cache_index_path():
    return Path(current_app.config["OUTPUT_FOLDER"]) / CACHE_INDEX_FILENAME


def load_cache_index():
    cache_path = get_cache_index_path()
    if not cache_path.exists():
        return {}

    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_cache_index(cache_index):
    cache_path = get_cache_index_path()
    cache_path.write_text(json.dumps(cache_index, indent=2), encoding="utf-8")


def build_cache_key(file_bytes, job_description):
    digest = hashlib.sha256()
    digest.update(file_bytes)
    digest.update(b"\0")
    digest.update(job_description.encode("utf-8"))
    return digest.hexdigest()


def build_output_prefix(filename, cache_key):
    safe_name = secure_filename(filename or "resume")
    stem = Path(safe_name).stem or "resume"
    return f"{stem}_{cache_key[:8]}"


def get_requested_output_format():
    requested_format = (
        request.form.get("output_format")
        or request.args.get("output_format")
        or request.args.get("format")
        or "json"
    )
    return OUTPUT_FORMAT_ALIASES.get(requested_format.strip().lower())


def read_output_file(filename):
    if not filename:
        return None

    output_path = Path(current_app.config["OUTPUT_FOLDER"]) / filename
    if not output_path.is_file():
        return None

    return output_path.read_text(encoding="utf-8")


def read_cached_report(cache_entry, output_format):
    output_folder = Path(current_app.config["OUTPUT_FOLDER"])
    json_report = cache_entry.get("json_report")
    markdown_report = cache_entry.get("markdown_report")

    if not json_report:
        return None

    json_path = output_folder / json_report
    if not json_path.is_file():
        return None

    report = json.loads(json_path.read_text(encoding="utf-8"))
    return build_formatted_analysis_response(
        report,
        cached=True,
        original_filename=cache_entry.get("original_filename"),
        output_format=output_format,
        json_report=json_report,
        markdown_report=markdown_report,
    )


def build_analysis_response(
    report,
    cached,
    original_filename,
    json_report=None,
    markdown_report=None,
):
    report_files = report.get("report_files", {})
    json_report = json_report or report_files.get("json")
    markdown_report = markdown_report or report_files.get("markdown")

    return {
        "success": True,
        "cached": cached,
        "source_file": original_filename,
        "candidate_name": report.get("candidate_name"),
        "candidate_email": report.get("candidate_email"),
        "overall_scores": report.get("overall_scores", {}),
        "professional_summary": report.get("professional_summary", ""),
        "key_value_proposition": report.get("key_value_proposition", ""),
        "missing_skills": report.get("missing_critical_skills", []),
        "recommended_keywords": report.get("recommended_keywords", []),
        "top_improvements": report.get("top_improvements", []),
        "section_scores": report.get("section_scores", {}),
        "report_files": {
            "json": json_report,
            "markdown": markdown_report,
        },
        "download_urls": {
            "json": f"/reports/{json_report}" if json_report else None,
            "markdown": f"/reports/{markdown_report}" if markdown_report else None,
        },
    }


def build_formatted_analysis_response(
    report,
    cached,
    original_filename,
    output_format,
    json_report=None,
    markdown_report=None,
):
    json_body = build_analysis_response(
        report,
        cached=cached,
        original_filename=original_filename,
        json_report=json_report,
        markdown_report=markdown_report,
    )

    if output_format == "json":
        return jsonify(json_body)

    markdown = read_output_file(json_body["report_files"].get("markdown"))
    if markdown is None:
        return jsonify({"error": "Markdown report is unavailable"}), 500

    return Response(
        markdown,
        content_type="text/markdown; charset=utf-8",
        headers={
            "X-Resume-Analysis-Cached": str(cached).lower(),
            "X-Resume-Source-File": original_filename or "",
            "X-Resume-Json-Report": json_body["report_files"].get("json") or "",
            "X-Resume-Markdown-Report": json_body["report_files"].get("markdown") or "",
        },
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
    return render_template('index.html')


@bp.route('/api', methods=['GET'])
def api_index():
    return jsonify({
        "message": "AI Resume Intelligence API is running",
        "endpoints": {
            "ui": "/",
            "health": "/health",
            "analyze": "/analyze",
            "extract_only": "/extract-only",
            "reports": "/reports",
            "download_report": "/reports/<filename>",
        },
        "analyze_usage": {
            "method": "POST",
            "content_type": "multipart/form-data",
            "fields": {
                "resume": "PDF or DOCX file",
                "job_description": "Job description text",
                "output_format": "json or markdown",
            },
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
    output_format = get_requested_output_format()
    if not output_format:
        return jsonify({"error": "output_format must be json or markdown"}), 400

    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    job_description = request.form.get('job_description', '')
    file_path = None

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and DOCX files allowed"}), 400

    file_bytes = file.read()
    file.stream.seek(0)
    cache_key = build_cache_key(file_bytes, job_description)
    cache_index = load_cache_index()
    cached_response = read_cached_report(cache_index.get(cache_key, {}), output_format)
    if cached_response:
        return cached_response

    try:
        file_path = save_upload(file)

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
        output_prefix = build_output_prefix(file.filename, cache_key)
        final_report = report_gen.generate_full_report(
            resume, ats_result, match_result, skill_gap,
            section_eval, summary, improvements, keywords_opt, job_description,
            filename_prefix=output_prefix,
        )

        report_files = final_report.get("report_files", {})
        cache_index[cache_key] = {
            "original_filename": file.filename,
            "json_report": report_files.get("json"),
            "markdown_report": report_files.get("markdown"),
            "created_at": final_report.get("report_generated_at")
            or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_cache_index(cache_index)

        return build_formatted_analysis_response(
            final_report,
            cached=False,
            original_filename=file.filename,
            output_format=output_format,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if file_path:
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
    if Path(filename).name != filename:
        return jsonify({"error": "Report names cannot include folders"}), 400

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
