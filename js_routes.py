from flask import Blueprint, send_from_directory
import os

js_routes = Blueprint('js_routes', __name__)

@js_routes.route('/js_routes/<path:filename>')
def serve_js(filename):
    return send_from_directory('.', filename)
