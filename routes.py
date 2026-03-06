
from flask import Blueprint, send_from_directory, jsonify
import os

routes = Blueprint('routes', __name__)

@routes.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@routes.route('/Gore/output/<path:filename>')
def serve_png(filename):
    return send_from_directory(os.path.join('Gore', 'output'), filename)

# New route to list all PNGs in Gore/output
@routes.route('/Gore/output/list_pngs')
def list_pngs():
    output_dir = os.path.join('Gore', 'output')
    pngs = [f for f in os.listdir(output_dir) if f.lower().endswith('.png')]
    return jsonify(pngs)
