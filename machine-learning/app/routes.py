from flask import current_app, request, Blueprint, jsonify

bp = Blueprint('main', __name__)

@bp.route('/predict', methods=['POST'])
def predict():
    """Predict P and S waves using specified model (custom or phasenet)"""
    data = request.get_json()
    
    # Extract model_type parameter, default to 'custom'
    model_type = data.get('model_type', 'custom')
    
    # Remove model_type from data before passing to handlers
    predict_data = {k: v for k, v in data.items() if k != 'model_type'}
    
    if model_type.lower() == 'phasenet':
        # Use PhaseNet handler
        phasenet_handler = current_app.extensions.get("phasenet_handler")
        
        if phasenet_handler is None:
            return jsonify({
                "error": "PhaseNet handler not available",
                "message": "PhaseNet model failed to initialize. Check server logs for details.",
                "station_code": data.get("station_code", "unknown"),
                "p_arr": False,
                "p_arr_time": data.get("start_time", "1970-01-01 00:00:00"),
                "p_arr_index": -1,
                "s_arr": False,
                "s_arr_time": data.get("start_time", "1970-01-01 00:00:00"),
                "s_arr_index": -1,
                "model_type": "phasenet_unavailable"
            }), 503
        
        return phasenet_handler.predict(**predict_data)
    
    else:
        # Use custom model handler (default)
        prediction_handler = current_app.extensions.get("prediction_handler")
        return prediction_handler.predict(**predict_data)

@bp.route('/predict/stats', methods=['POST'])
def predict_stats():
    """Predict earthquake statistics using custom model"""    
    prediction_handler = current_app.extensions.get("prediction_handler")

    return prediction_handler.predict_stats(
        **request.get_json()
    )
