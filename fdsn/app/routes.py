from flask import current_app, request, Blueprint

bp = Blueprint('main', __name__)

@bp.route('/run', methods=['POST'])
def run():
    trace_handler = current_app.extensions.get("trace_handler")

    return trace_handler.run(
        **request.get_json()
    )

@bp.route('/stop', methods=['POST'])
def stop():
    trace_handler = current_app.extensions.get("trace_handler")

    return trace_handler.stop(
        **request.get_json()
    )
