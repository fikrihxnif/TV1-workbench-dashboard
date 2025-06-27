# Trend Vision One Workbench Alert Dashboard

A Flask web application for **monitoring and visualizing alerts** from Trend Vision One XDR.  
It fetches alert data via the Trend Vision One API, categorizes it by status, and presents summary metrics on a dashboard and through JSON API endpoints.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.x-green.svg)

---

## 🚀 Features

- **API Integration:** Retrieves alert data from Trend Vision One XDR API.
- **In-Memory Caching:** Keeps data in memory and refreshes every **1 minute** for fast responses.
- **Alert Categorization:** Metrics by status (`Open`, `In Progress`, `Closed`), by model, and by investigation result.
- **REST API Endpoints:** Expose alert data for external tools or further analysis.
- **Simple Dashboard:** HTML dashboard for easy visualization.
- **Background Threading:** Automatic data refresh with no manual intervention.

---

## 🛠️ Requirements

- Python 3.8+
- Flask
- requests

Install dependencies:

```bash
pip install flask requests
```

---

## ⚙️ Setup
1. Clone this repository:

```bash
git clone https://github.com/fikrihxnif/TV1-workbench-dashboard.git
cd TV1-workbench-dashboard
```
2. Configure your API token:
Edit the script and replace the value of API_TOKEN:

```bash
API_TOKEN = 'YOUR_TREND_VISION_ONE_API_TOKEN'
```
3. Templates:
   Make sure dashboard_scroll3.html is in the templates/ directory.

4. Run the Flask server:

```bash
python workbench_dashboard.py
```
The app will run at http://127.0.0.1:5000/

---

## 🗂️ How Caching Works
- The application refreshes its in-memory cache every 1 minute (60 seconds) using a background thread.

- Cache interval can be changed by modifying the time.sleep(60) line in the script.

---

## 🔐 Security & Notes
- Keep your API token secret!

- For internal use only—restrict access to the dashboard as needed.

- For production, run behind a secure reverse proxy (e.g., NGINX) and use HTTPS.

---

## 🛡️ Customization
- Cache Interval:
  Change the refresh frequency by adjusting time.sleep(60) (in seconds).

- More Metrics:
  Add new endpoints by defining new Flask routes in the script.

---

## 🤝 Support
For issues, questions, or feature requests, please contact your SOC or IT development team.

---

Happy monitoring!
