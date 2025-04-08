from flask import current_app, request, Blueprint

bp = Blueprint('main', __name__)

@bp.route('/predict', methods=['POST'])
def predict():  # put application's code here
    prediction_handler = current_app.extensions.get("prediction_handler")

    return prediction_handler.predict(
        **request.get_json()
    )

@bp.route('/predict/stats', methods=['POST'])
def predict_stats():
    prediction_handler = current_app.extensions.get("prediction_handler")

    return prediction_handler.predict_stats(
        **request.get_json()
    )
