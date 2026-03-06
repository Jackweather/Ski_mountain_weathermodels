import os
import requests
import datetime
import pygrib
import matplotlib.pyplot as plt
import pytz
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# -----------------------------
# HRRR RUN VALIDATION
# -----------------------------

def get_latest_run_with_fallback():
    est = pytz.timezone("US/Eastern")
    now = datetime.datetime.now(pytz.utc).astimezone(est)
    run_start_hours = {
        21: "00",
        3: "06",
        9: "12",
        15: "18"
    }
    available_hours = list(run_start_hours.keys())
    most_recent_run_time = None
    for offset in range(24):
        candidate_time = now - datetime.timedelta(hours=offset)
        candidate_hour = candidate_time.hour
        if candidate_hour in available_hours:
            candidate_date = candidate_time.strftime("%Y%m%d")
            candidate_run = run_start_hours[candidate_hour]
            if validate_run(candidate_date, candidate_run):
                most_recent_run_time = candidate_time
                break
    if most_recent_run_time is None:
        raise ValueError("No valid HRRR run time found in last 24 hours")
    return (
        most_recent_run_time.strftime("%Y%m%d"),
        run_start_hours[most_recent_run_time.hour]
    )

# -----------------------------
# VALIDATE RUN
# -----------------------------

def validate_run(date, run):
    test_url = (
        f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/"
        f"hrrr.{date}/conus/hrrr.t{run}z.wrfsfcf00.grib2"
    )
    try:
        response = requests.head(test_url, timeout=5)
        return response.status_code == 200
    except:
        return False

# -----------------------------
# DOWNLOAD SNOD GRIB FILE
# -----------------------------

def download_grib_file_task(args):
    date, run, forecast_hour = args
    base_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl"
    params = {
        "dir": f"/hrrr.{date}/conus",
        "file": f"hrrr.t{run}z.wrfsfcf{forecast_hour:02d}.grib2",
        "var_SNOD": "on",
        "lev_surface": "on"
    }
    response = requests.get(base_url, params=params, stream=True)
    if response.status_code == 200:
        grib_dir = os.path.join("HRRR", "Gore", "grib_files_snod")
        if not os.path.exists(grib_dir):
            os.makedirs(grib_dir, exist_ok=True)
        file_path = os.path.join(grib_dir, f"hrrr.t{run}z.f{forecast_hour:02d}.grib2")
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        return file_path
    return None

# -----------------------------
# EXTRACT SNOD AT GORE
# -----------------------------

def extract_gore_snod(grib_file, gore_coords):
    with pygrib.open(grib_file) as grbs:
        for grb in grbs:
            if (grb.name == "Snow depth" or grb.shortName == "sd"):
                lats, lons = grb.latlons()
                values = grb.values
                dist = np.sqrt((lats - gore_coords[0])**2 + (lons - gore_coords[1])**2)
                min_idx = np.unravel_index(np.argmin(dist), dist.shape)
                gore_val_m = values[min_idx]  # HRRR is in meters
                gore_val_in = gore_val_m * 39.3701  # Convert meters to inches
                return max(round(gore_val_in, 2), 0)  # Only positive change
    return None

# -----------------------------
# 12 HOUR FORMAT
# -----------------------------

def convert_to_12_hour(hour):
    utc_to_local = {
        18: 13,
        0: 19,
        6: 1,
        12: 7
    }
    local_hour = utc_to_local.get(hour, hour)
    period = "AM" if local_hour < 12 else "PM"
    local_hour = local_hour % 12
    if local_hour == 0:
        local_hour = 12
    return f"{local_hour} {period}"

# -----------------------------
# CHART GENERATION
# -----------------------------

def generate_snod_chart(forecast_data, output_dir, start_date, start_hour, run):
    snods = [d["snod_in"] for d in forecast_data]
    times = [convert_to_12_hour((start_hour + i) % 24) for i in range(len(forecast_data))]
    plt.figure(figsize=(10,6))
    plt.plot(range(len(snods)), snods, marker="o")
    plt.ylim(bottom=0)  # Always start y-axis at zero
    run_label = run
    plt.title(f"Gore Mountain Snow Depth Change (HRRR model - Run {run_label}z)", fontsize=16)
    plt.ylabel("Snow Depth Change (inches)", fontsize=14)
    day_marker_colors = ['red', 'orange', 'blue', 'green', 'purple']
    current_day = 0
    for i, data in enumerate(forecast_data):
        if (start_hour + i) % 24 == 0:
            plt.axvline(
                x=i,
                color=day_marker_colors[current_day % len(day_marker_colors)],
                linestyle='--',
                linewidth=0.8,
                label=f"{start_date}"
            )
            start_date = (datetime.datetime.strptime(start_date, "%Y%m%d") + datetime.timedelta(days=1)).strftime("%Y%m%d")
            current_day += 1
    tick_indices = [0] + list(range(2, len(times), 2))
    tick_labels = [times[i] for i in tick_indices]
    plt.xticks(tick_indices, tick_labels, fontsize=7)
    plt.legend(loc="upper left", fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    chart_path = os.path.join(
        output_dir,
        "gore_mountain_snow_depth_change.png"
    )
    # Move old PNG to 'old' subfolder, keeping only the last one
    old_dir = os.path.join(output_dir, "old")
    if not os.path.exists(old_dir):
        os.makedirs(old_dir, exist_ok=True)
    if os.path.exists(chart_path):
        # Remove any previous file in 'old' folder
        old_pngs = [f for f in os.listdir(old_dir) if f.endswith(".png")]
        for old_png in old_pngs:
            os.remove(os.path.join(old_dir, old_png))
        # Move the current PNG to 'old'
        import shutil
        shutil.move(chart_path, os.path.join(old_dir, "gore_mountain_snow_depth_change.png"))
    plt.savefig(chart_path)
    plt.close()
    print(f"Line chart saved to {chart_path}")

# -----------------------------
# MAIN FUNCTION
# -----------------------------


def generate_gore_snod_forecast():
    gore_coords = (43.6733, -74.0068)  # Gore Mountain latitude, longitude
    date, run = get_latest_run_with_fallback()
    forecast_data = []
    run_start_hours = {
        "00": 19,
        "06": 1,
        "12": 7,
        "18": 13
    }
    start_hour = run_start_hours.get(run, 0)
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [(date, run, hour) for hour in range(0, 48)]
        grib_files = list(executor.map(download_grib_file_task, tasks))
    prev_snod = None
    cumulative = 0
    for hour, grib_file in enumerate(grib_files):
        if grib_file:
            snod_val = extract_gore_snod(grib_file, gore_coords)  # now in inches
            if prev_snod is not None and snod_val is not None:
                snod_change = max(snod_val - prev_snod, 0)
            else:
                snod_change = 0
            prev_snod = snod_val if snod_val is not None else prev_snod
            if snod_change > 0:
                cumulative += snod_change
            else:
                cumulative = 0
            local_hour_24 = (start_hour + hour) % 24
            local_hour_12 = convert_to_12_hour(local_hour_24)
            day_offset = (start_hour + hour) // 24
            day_label = f"Day {day_offset + 1}"
            forecast_data.append({
                "hour": f"{day_label} {local_hour_12}",
                "snod_in": cumulative
            })
        else:
            cumulative = 0
            local_hour_24 = (start_hour + hour) % 24
            local_hour_12 = convert_to_12_hour(local_hour_24)
            day_offset = (start_hour + hour) // 24
            day_label = f"Day {day_offset + 1}"
            forecast_data.append({
                "hour": f"{day_label} {local_hour_12}",
                "snod_in": 0
            })
    output_dir = os.path.join("HRRR", "Gore", "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    generate_snod_chart(forecast_data, output_dir, date, start_hour, run)
    grib_dir = os.path.join("HRRR", "Gore", "grib_files_snod")
    if os.path.exists(grib_dir):
        for grib_file in os.listdir(grib_dir):
            os.remove(os.path.join(grib_dir, grib_file))
        os.rmdir(grib_dir)

if __name__ == "__main__":
    grib_dir = os.path.join("HRRR", "Gore", "grib_files_snod")
    if os.path.exists(grib_dir):
        for grib_file in os.listdir(grib_dir):
            os.remove(os.path.join(grib_dir, grib_file))
        os.rmdir(grib_dir)
    generate_gore_snod_forecast()
