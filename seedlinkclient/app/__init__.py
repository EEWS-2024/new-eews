from flask import Flask

from app.handlers.trace_handler import TraceHandler

def create_app():
    app = Flask(__name__)

    trace_handler = TraceHandler()

    app.extensions = getattr(app, "extensions", {})
    app.extensions["trace_handler"] = trace_handler

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
