import threading
from flask import Blueprint

def run_scripts(scripts, delay):
    import subprocess
    import time
    for script, cwd in scripts:
        subprocess.Popen(["python", script], cwd=cwd)
        time.sleep(delay)

run_task1_bp = Blueprint('run_task1_bp', __name__)

@run_task1_bp.route("/run-task1")
def run_task1():
    scripts = [
        ("/opt/render/project/src/NY/mslp_prate_csnow_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/tmp_2m_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/Snow_liquid_ratio_8to1_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/Snow_liquid_ratio_10to1_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/wind_10m_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/total_precip_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/vis_EAST.py", "/opt/render/project/src/NY"),
        ("/opt/render/project/src/NY/Snow_liquid_ratio_SNOD_EAST.py", "/opt/render/project/src/NY"),
    ]
    threading.Thread(target=lambda: run_scripts(scripts, 3)).start()
    return "Task started in background! Check logs folder for output.", 200
