# plotter.py
# Generates simple ASCII-style plots for the Space Weather Dashboard

from datetime import datetime
from typing import List

# Unicode sparkline characters (low to high)
_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _normalize(values: List[float], length: int = len(_SPARK_CHARS)) -> List[int]:
    """Normalize list of floats to integer indices between 0 and length-1."""
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        mid = length // 2
        return [mid] * len(values)
    rng = vmax - vmin
    return [int((v - vmin) / rng * (length - 1)) for v in values]


def sparkline(values: List[float]) -> str:
    """Return a small sparkline string for the given list of values."""
    idxs = _normalize(values)
    return "".join(_SPARK_CHARS[i] for i in idxs)


def create_wind_speed_plot(wind_data: list) -> str:
    """Create a compact text plot for solar wind speed."""
    if not wind_data:
        return "No wind data available."

    recent = wind_data[-30:]
    times, speeds = [], []

    for entry in recent:
        time_tag = entry.get("time_tag")
        speed = entry.get("speed")
        if not time_tag or speed is None:
            continue

        try:
            # Accept both NASA formats
            if "T" in time_tag:
                dt = datetime.strptime(time_tag.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            else:
                dt = datetime.strptime(time_tag.split(".")[0], "%Y-%m-%d %H:%M:%S")
            times.append(dt.strftime("%H:%M"))
        except Exception:
            times.append(time_tag[:8])

        try:
            speeds.append(float(speed))
        except (ValueError, TypeError):
            continue

    if not speeds:
        return "No valid data to plot."

    sline = sparkline(speeds)

    vmin = min(speeds)
    vmax = max(speeds)
    median = speeds[len(speeds) // 2] if speeds else 0.0

    left_time = times[0] if times else ""
    right_time = times[-1] if times else ""

    # Build multi-line ASCII block
    lines = [
        "",
        f" Speed (km/s)  {sline}",
        f" Min: {vmin:.1f}    Median: {median:.1f}    Max: {vmax:.1f}",
        f" Time: {left_time}     {right_time}",
        ""
    ]
    return "\n".join(lines)
