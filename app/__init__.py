from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.jinja_env.auto_reload = True

    # Register Blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app