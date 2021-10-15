
from .database import init as initialize_database
from .endpoints.v1 import blueprint as v1_endpoints

from flask import Flask


def create_app(config=None):

    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE="sqlite:///mrd-storage.sqlite",
        JSONIFY_PRETTYPRINT_REGULAR=True,
    )
    app.config.update(config or {})

    initialize_database(app.config['DATABASE'])

    app.register_blueprint(v1_endpoints)

    return app
