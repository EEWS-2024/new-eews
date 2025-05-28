from flask import Flask
from flask.cli import load_dotenv

from app.extensions import db, init_redis
from app.handlers.prediction import PredictionHandler

load_dotenv()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize the database with the app
    db.init_app(app)
    redis = init_redis()

    prediction_handler = PredictionHandler(
        redis=redis,
        db=db
    )
    
    # Initialize PhaseNet handler
    phasenet_handler = None
    try:
        from app.handlers.phasenet_handler import PhaseNetHandler
        phasenet_handler = PhaseNetHandler()
        print("PhaseNet handler initialized successfully")
    except Exception as e:
        print(f"Failed to initialize PhaseNet handler: {e}")
        phasenet_handler = None

    app.extensions = getattr(app, "extensions", {})
    app.extensions["redis"] = redis
    app.extensions["prediction_handler"] = prediction_handler
    app.extensions["phasenet_handler"] = phasenet_handler

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
