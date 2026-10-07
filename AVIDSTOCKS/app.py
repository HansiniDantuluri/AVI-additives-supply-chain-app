import os
import importlib
from flask import Flask

from config import Config
from routes.extensions import bcrypt, mail


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    app.secret_key = os.environ.get('SECRET_KEY')

    bcrypt.init_app(app)
    mail.init_app(app)

    blueprints = {
        'routes.auth': 'auth_bp',
        'routes.dashboard': 'dashboard_bp',
        'routes.alerts': 'alerts_bp',
        'routes.materials': 'materials_bp',
        'routes.batches': 'batches_bp',
        'routes.orders': 'orders_bp',
        'routes.reports': 'reports_bp',
    }

    for module_name, bp_name in blueprints.items():
        try:
            mod = importlib.import_module(module_name)
            bp = getattr(mod, bp_name)
            app.register_blueprint(bp)
        except ModuleNotFoundError:
            continue
        except AttributeError:
            continue

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)