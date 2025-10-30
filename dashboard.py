import os
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from data_fetcher import DataFetcher
from plotter import create_wind_speed_plot

NASA_API_KEY = os.getenv("NASA_API_KEY", "7GUP3JCEQIYFgN4tdlUtD6AJ2W4zvXEJbp2Pe6KD")


# ---------- Layout ----------
def create_layout():
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="left", size=50),
        Layout(name="center", ratio=2),
        Layout(name="right", size=50),
    )

    layout["left"].split(Layout(name="solar_wind"), Layout(name="geomagnetic"))
    layout["center"].split(Layout(name="cme"), Layout(name="solar_flares"), Layout(name="alerts"))
    layout["right"].split(Layout(name="sunspots"), Layout(name="solar_flux"), Layout(name="geomag_storms"))
    return layout


# ---------- Panels ----------
def header():
    title = Text("🚀 Space Weather CLI Dashboard", style="bold cyan", justify="center")
    return Panel(title, border_style="bright_blue")


def footer():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return Panel(Text(f"Last Updated: {now}", justify="center", style="dim"), border_style="green")


def solar_wind_panel(data):
    if not data:
        return Panel("No solar wind data available.", title="Solar Wind", border_style="red")

    latest = data[-1]
    speed = latest.get("speed", 0)
    density = latest.get("density", 0)
    chart = create_wind_speed_plot(data)

    text = Text.from_ansi(chart)
    text.append(f"\nSpeed: {speed:.1f} km/s\nDensity: {density:.2f} p/cm³", style="bold")
    return Panel(Align.center(text), title="Solar Wind (ACE)", border_style="blue")


def geomagnetic_panel(data):
    if not data:
        return Panel("No K-index data available.", title="Geomagnetic Activity", border_style="yellow")

    recent = data[-1]
    kp = float(recent.get("k_index", 0))
    level = "Quiet" if kp < 4 else "Active" if kp < 6 else "Storm"
    bar = "█" * int(kp) + "░" * (9 - int(kp))

    text = Text(f"Kp Index: {kp:.1f}/9\nStatus: {level}\n[{bar}]")
    return Panel(text, title="Geomagnetic K-Index", border_style="yellow")


def solar_flux_panel(data):
    if not data:
        return Panel("No solar flux data available.", title="Solar Flux", border_style="magenta")

    today = float(data[-1].get("flux", 0))
    yesterday = float(data[-2].get("flux", 0)) if len(data) > 1 else today
    trend = "🔺" if today > yesterday else "🔻" if today < yesterday else "➡️"

    text = Text(f"F10.7 cm Flux: {today:.1f} sfu\nYesterday: {yesterday:.1f} sfu\nTrend: {trend}")
    return Panel(text, title="Solar Flux Index", border_style="magenta")


def sunspot_panel(data):
    if not data:
        return Panel("No sunspot data available.", title="Sunspots", border_style="yellow")

    total_spots = sum(r.get("spot_count", 0) for r in data)
    regions = len(data)
    text = Text(f"Active Regions: {regions}\nTotal Sunspots: {total_spots}")
    return Panel(text, title="Sunspot Regions", border_style="yellow")


def cme_panel(data):
    table = Table(title="Recent Coronal Mass Ejections", title_style="bold cyan")
    table.add_column("Start Time", style="green")
    table.add_column("Location", style="yellow")
    table.add_column("Link", style="cyan", overflow="fold")

    if not data:
        table.add_row("No recent CME data.", "", "")
    else:
        for e in data[:5]:
            table.add_row(
                e.get("startTime", "N/A"),
                e.get("sourceLocation", "N/A"),
                f"[link={e.get('link', '#')}]Details[/link]",
            )
    return Panel(table, border_style="cyan")


def solar_flare_panel(data):
    table = Table(title="Recent Solar Flares", title_style="bold red")
    table.add_column("Start", style="green")
    table.add_column("Class", style="yellow")
    table.add_column("Location", style="cyan")
    table.add_column("Link", style="blue", overflow="fold")

    if not data:
        table.add_row("No recent flare data.", "", "", "")
    else:
        for f in data:
            table.add_row(
                f.get("beginTime", "N/A"),
                f.get("classType", "N/A"),
                f.get("sourceLocation", "N/A"),
                f"[link={f.get('link', '#')}]Details[/link]",
            )
    return Panel(table, border_style="red")


def geomag_storm_panel(data):
    table = Table(title="Recent Geomagnetic Storms", title_style="bold green")
    table.add_column("Start Time", style="cyan")
    table.add_column("Kp Index", style="magenta")
    table.add_column("Link", style="blue", overflow="fold")

    if not data:
        table.add_row("No recent storms found.", "", "")
    else:
        for s in data:
            table.add_row(
                s.get("startTime", "N/A"),
                str(s.get("kpIndex", "N/A")),
                f"[link={s.get('link', '#')}]Details[/link]",
            )
    return Panel(table, border_style="green")


def alerts_panel(data):
    if not data:
        return Panel("No recent space weather alerts.", title="Alerts", border_style="red")

    text = Text()
    for alert in data[:5]:
        msg_type = alert.get("messageType", "Alert")
        date = alert.get("messageIssueTime", "N/A")[:10]
        text.append(f"- {msg_type} ({date})\n", style="bold")
    return Panel(text, title="Space Weather Alerts", border_style="red")


# ---------- Main Loop ----------
def main():
    console = Console()
    fetcher = DataFetcher(NASA_API_KEY)
    layout = create_layout()

    layout["header"].update(header())
    layout["footer"].update(footer())

    with Live(layout, screen=True, refresh_per_second=0.5):
        while True:
            try:
                # Time range for NASA endpoints (7 days)
                end = datetime.utcnow().strftime("%Y-%m-%d")
                start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

                # Fetch data
                wind = fetcher.get_solar_wind_data()
                geomag = fetcher.get_geomagnetic_index()
                flux = fetcher.get_solar_flux()
                sunspots = fetcher.get_sunspot_data()
                cmes = fetcher.get_cme_events(start, end)
                flares = fetcher.get_solar_flares(start, end)
                storms = fetcher.get_geomagnetic_storms(start, end)
                alerts = fetcher.get_space_weather_alerts()

                # Update panels
                layout["solar_wind"].update(solar_wind_panel(wind))
                layout["geomagnetic"].update(geomagnetic_panel(geomag))
                layout["solar_flux"].update(solar_flux_panel(flux))
                layout["sunspots"].update(sunspot_panel(sunspots))
                layout["cme"].update(cme_panel(cmes))
                layout["solar_flares"].update(solar_flare_panel(flares))
                layout["geomag_storms"].update(geomag_storm_panel(storms))
                layout["alerts"].update(alerts_panel(alerts))
                layout["footer"].update(footer())

                time.sleep(180)  # refresh every 3 min

            except KeyboardInterrupt:
                console.print("\nDashboard closed.", style="bold red")
                break
            except Exception as e:
                console.print(f"⚠️ Error updating dashboard: {e}", style="bold red")
                time.sleep(30)


if __name__ == "__main__":
    main()
