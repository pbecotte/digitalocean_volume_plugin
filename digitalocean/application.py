import os

from flask import Flask

from .exceptions import APIException
from .do_api import api_get_metadata


def make_app(config=None):
    app = Flask(__name__)

    if config is None:
        class DefaultConfig(object):
            DROPLET_ID, REGION = api_get_metadata()
            TOKEN = os.environ['DIGITAL_OCEAN_TOKEN']
        config = DefaultConfig

    for att in ['DROPLET_ID', 'REGION', 'TOKEN']:
        if not hasattr(config, att):
            raise APIException('Config missing required value %s' % att)

    app.config.from_object(config)
    app.config['VOLUME_MOUNTS'] = {}

    register_views(app)
    return app

def register_views(app):
    from .controllers import routes
    app.register_blueprint(routes)
