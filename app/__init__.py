from flask import Flask
from flask_cors import CORS
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Register Blueprints
    from app.routes import main
    from app.routes.papers import papers_bp
    from app.routes.chat import chat_bp

    app.register_blueprint(main)
    app.register_blueprint(papers_bp)
    app.register_blueprint(chat_bp)

    return app