import requests
from datetime import datetime, timedelta


class DataFetcher:
    """Handles data retrieval from NASA and NOAA space weather APIs."""

    def __init__(self, nasa_api_key: str):
        if not nasa_api_key:
            raise ValueError("NASA API key is required.")
        self.nasa_api_key = nasa_api_key
        self.nasa_base = "https://api.nasa.gov/DONKI/"
        self.noaa_base = "https://services.swpc.noaa.gov/"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SpaceWeatherDashboard/2.0"})

    def _make_request(self, url, params=None):
        """Perform safe GET request."""
        try:
            res = self.session.get(url, params=params, timeout=12)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed: {e}")
            return None

    # ---------- NASA: DONKI DATA ----------

    def get_cme_events(self, start_date: str, end_date: str):
        """Fetch Coronal Mass Ejection (CME) events from NASA."""
        url = self.nasa_base + "CME"
        params = {"startDate": start_date, "endDate": end_date, "api_key": self.nasa_api_key}
        data = self._make_request(url, params=params)
        if not data:
            return None

        events = []
        for e in data:
            events.append({
                "startTime": e.get("startTime"),
                "sourceLocation": e.get("sourceLocation"),
                "catalog": e.get("catalog"),
                "link": e.get("link", "")
            })
        return events[:5]  # return only recent top events

    def get_solar_flares(self, start_date: str, end_date: str):
        """Fetch Solar Flare (FLR) data from NASA."""
        url = self.nasa_base + "FLR"
        params = {"startDate": start_date, "endDate": end_date, "api_key": self.nasa_api_key}
        data = self._make_request(url, params=params)
        if not data:
            return None

        flares = []
        for f in data:
            flares.append({
                "beginTime": f.get("beginTime"),
                "peakTime": f.get("peakTime"),
                "classType": f.get("classType"),
                "sourceLocation": f.get("sourceLocation"),
                "link": f.get("link", "")
            })
        return flares[:5]

    def get_geomagnetic_storms(self, start_date: str, end_date: str):
        """Fetch Geomagnetic Storm (GST) data from NASA."""
        url = self.nasa_base + "GST"
        params = {"startDate": start_date, "endDate": end_date, "api_key": self.nasa_api_key}
        data = self._make_request(url, params=params)
        if not data:
            return None

        storms = []
        for s in data:
            kp_index = None
            if s.get("allKpIndex"):
                kp_index = s["allKpIndex"][0].get("kpIndex")
            storms.append({
                "startTime": s.get("startTime"),
                "kpIndex": kp_index,
                "link": s.get("link", "")
            })
        return storms[:5]

    def get_space_weather_alerts(self):
        """Fetch latest space weather alerts/notifications from NASA."""
        url = self.nasa_base + "notifications"
        params = {"type": "all", "api_key": self.nasa_api_key}
        data = self._make_request(url, params=params)
        if not data:
            return None

        alerts = []
        for a in data[:5]:
            alerts.append({
                "messageType": a.get("messageType"),
                "messageIssueTime": a.get("messageIssueTime"),
                "messageBody": a.get("messageBody", "")[:200] + "..."
            })
        return alerts

    # ---------- NOAA: LIVE SPACE WEATHER ----------

    def get_solar_wind_data(self):
        """Get real-time solar wind data (ACE) from NOAA."""
        url = self.noaa_base + "json/rtsw/rtsw_wind_1m.json"
        data = self._make_request(url)
        if not isinstance(data, list):
            return None

        result = []
        for d in data:
            try:
                speed = float(d.get("proton_speed", 0))
                density = float(d.get("proton_density", 0))
                if speed > 0:
                    result.append({
                        "time_tag": d.get("time_tag"),
                        "speed": speed,
                        "density": density
                    })
            except Exception:
                continue
        return result[-60:] if result else None

    def get_sunspot_data(self):
        """Fetch sunspot report from NOAA."""
        url = self.noaa_base + "json/sunspot_report.json"
        return self._make_request(url)

    def get_geomagnetic_index(self):
        """Fetch 1-minute K-index values from NOAA."""
        url = self.noaa_base + "json/planetary_k_index_1m.json"
        data = self._make_request(url)
        if not isinstance(data, list):
            return None
        return data[-20:] if data else None

    def get_solar_flux(self):
        """Fetch solar flux index (F10.7 cm) from NOAA."""
        url = self.noaa_base + "json/f10_7cm.json"
        data = self._make_request(url)
        if not isinstance(data, list):
            return None
        return data[-5:] if data else None


# ✅ Example usage:
if __name__ == "__main__":
    nasa_api_key = "7GUP3JCEQIYFgN4tdlUtD6AJ2W4zvXEJbp2Pe6KD"
    df = DataFetcher(nasa_api_key)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    print("Fetching NASA CME events...")
    print(df.get_cme_events(week_ago, today))

    print("\nFetching Solar Flares...")
    print(df.get_solar_flares(week_ago, today))

    print("\nFetching Geomagnetic Storms...")
    print(df.get_geomagnetic_storms(week_ago, today))

    print("\nFetching Space Weather Alerts...")
    print(df.get_space_weather_alerts())
