from app import create_app, db
from flask_migrate import Migrate
from asgiref.wsgi import WsgiToAsgi

app = create_app()
migrate = Migrate(app, db)

asgi_app = WsgiToAsgi(app)

