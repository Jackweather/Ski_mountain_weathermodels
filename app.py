from flask import Flask
from routes import routes
from js_routes import js_routes

app = Flask(__name__)

import threading
def run_scripts(scripts, delay):
    import subprocess
    import time
    for script, cwd in scripts:
        subprocess.Popen(["python", script], cwd=cwd)
        time.sleep(delay)

@app.route("/run-task1")
def run_task1():
    scripts = [
        ("HRRR/HRRR_10m_snod.py", "HRRR"),
        ("HRRR/HRRR_10m_tcdc.py", "HRRR"),
        ("HRRR/HRRR_10m_wind.py", "HRRR"),
        ("HRRR/HRRR_10m_vis.py", "HRRR"),
        ("HRRR/HRRR_10m_tmp.py", "HRRR")
    ]
    threading.Thread(target=lambda: run_scripts(scripts, 3)).start()
    return "Task started in background! Check logs folder for output.", 200

if __name__ == '__main__':
    app.run(debug=True)
