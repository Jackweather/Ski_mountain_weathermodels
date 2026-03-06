from flask import Flask
from routes import routes
from js_routes import js_routes
from run_task1_route import run_task1_bp

app = Flask(__name__)
app.register_blueprint(routes)
app.register_blueprint(js_routes)
app.register_blueprint(run_task1_bp)

if __name__ == '__main__':
    app.run(debug=True)