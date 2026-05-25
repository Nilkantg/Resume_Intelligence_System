from pathlib import Path
import sys

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)  # Allow frontend requests

    # Config
    app.config['UPLOAD_FOLDER'] = Path(__file__).resolve().parent / 'uploads'
    app.config['OUTPUT_FOLDER'] = PROJECT_ROOT / 'outputs'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

    # Ensure folders exist
    app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
    app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

    # Register routes
    from app.routes import bp
    app.register_blueprint(bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
