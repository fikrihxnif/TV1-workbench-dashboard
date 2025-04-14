from flask import Flask, render_template, jsonify, Response
import requests
from datetime import datetime, timezone, timedelta
import threading
import time

app = Flask(__name__)

# Replace with your Trend Vision One API token
API_TOKEN = 'YOUR API KEY'
BASE_URL = 'https://api.xdr.trendmicro.com' # according to your Trend Vision One region

# Headers for the API requests
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json'
}

# Global variable to store fetched data
data_cache = {
    "new_alerts": [],
    "inprogress_alerts": [],
    "closed_alerts": []
}

@app.route('/alerts-model')
def alerts_model():
    try:
        model_data = fetch_alerts_by_model()
        return jsonify(model_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def fetch_alerts_by_model():
    """
    Fetch all closed alerts since the previous Saturday and categorize them by model.
    """
    url = f"{BASE_URL}/v3.0/workbench/alerts"
    headers = HEADERS.copy()
    headers['TMV1-Filter'] = "status eq 'Closed'"
    alerts = []

    # Calculate the last Saturday
    now = datetime.now(timezone.utc)
    # Find the number of days to subtract to get to the last Saturday
    days_to_subtract = (now.weekday() - 5) % 7  # 5 is Saturday (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    last_saturday = now - timedelta(days=days_to_subtract)
    last_saturday = last_saturday.replace(hour=0, minute=0, second=0, microsecond=0)

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching closed alerts: {response.status_code}, {response.text}")
            return {"error": f"Error fetching closed alerts: {response.status_code}", "details": response.text}
        
        data = response.json()
        current_alerts = data.get('items', [])
        
        # Stop if all alerts in the current batch are older than last Saturday
        if not current_alerts or all(
            datetime.fromisoformat(alert['createdDateTime'].replace("Z", "+00:00")) < last_saturday
            for alert in current_alerts
        ):
            break
        
        # Append only relevant alerts
        alerts.extend([
            alert for alert in current_alerts
            if datetime.fromisoformat(alert['createdDateTime'].replace("Z", "+00:00")) >= last_saturday
        ])

        # Update the URL for the next page
        url = data.get('nextLink', None)

    # Categorize alerts by model
    model_counts = {}
    for alert in alerts:
        model = alert.get('model', 'Unknown')
        model_counts[model] = model_counts.get(model, 0) + 1

    print(f"Model counts: {model_counts}")  # Debugging: Print model distribution
    return model_counts


def fetch_closed_alerts_weekly():
    """
    Fetch all closed alerts since the previous Saturday and categorize them by investigation results.
    """
    url = f"{BASE_URL}/v3.0/workbench/alerts"
    headers = HEADERS.copy()
    headers['TMV1-Filter'] = "status eq 'Closed'"
    alerts = []

    # Calculate the last Saturday
    now = datetime.now(timezone.utc)
    last_saturday = now - timedelta(days=now.weekday() + 2)  # Previous Saturday
    last_saturday = last_saturday.replace(hour=0, minute=0, second=0, microsecond=0)

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching closed alerts: {response.status_code}, {response.text}")
            return {"error": f"Error fetching closed alerts: {response.status_code}", "details": response.text}
        
        data = response.json()
        current_alerts = data.get('items', [])
        
        # Stop if all alerts in the current batch are older than last Saturday
        if not current_alerts or all(
            datetime.fromisoformat(alert['createdDateTime'].replace("Z", "+00:00")) < last_saturday
            for alert in current_alerts
        ):
            break
        
        # Append only relevant alerts
        alerts.extend([
            alert for alert in current_alerts
            if datetime.fromisoformat(alert['createdDateTime'].replace("Z", "+00:00")) >= last_saturday
        ])

        # Debugging: Print the timestamp of the newest alert
        if current_alerts:
            newest_alert_time = current_alerts[0]['createdDateTime']
            print(f"Newest alert time in this batch: {newest_alert_time}")
        
        # Update the URL for the next page
        url = data.get('nextLink', None)

    # Initialize counts for known investigation results
    findings = {
        'True Positive': 0,
        'Benign True Positive': 0,
        'False Positive': 0,
        'Noteworthy': 0,
        'Others': 0
    }

    # Categorize alerts
    for alert in alerts:
        result = alert.get('investigationResult', 'Others')
        if result in findings:
            findings[result] += 1
        else:
            findings['Others'] += 1  # Safeguard for unexpected results

    print(f"Findings for the week: {findings}")  # Debugging: Print findings
    return findings

@app.route('/closed-alerts-weekly')
def closed_alerts_weekly():
    findings = fetch_closed_alerts_weekly()
    response = jsonify(findings)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/')
def dashboard():
    return render_template('dashboard_scroll3.html')

@app.route('/data')
def fetch_data():
    # Add elapsed time for all alerts
    new_alerts_with_time = [
        {**alert, "elapsedTime": calculate_time_elapsed(alert.get("createdDateTime"))}
        for alert in data_cache["new_alerts"]
    ]
    inprogress_alerts_with_time = [
        {**alert, "elapsedTime": calculate_time_elapsed(alert.get("createdDateTime"))}
        for alert in data_cache["inprogress_alerts"]
    ]
    return jsonify({
        'new_alerts': new_alerts_with_time,
        'inprogress_alerts': inprogress_alerts_with_time,
        'closed_alerts': data_cache["closed_alerts"]
    })

def fetch_alerts_by_status(target_statuses):
    """
    Fetch alerts filtered by their statuses using TMV1-Filter and sorted by severity via the orderBy parameter.
    :param target_statuses: A list of desired statuses to filter alerts by.
    :return: List of alerts with the specified statuses, including Workbench links.
    """
    url = f"{BASE_URL}/v3.0/workbench/alerts"

    # Construct the TMV1-Filter header using the correct syntax
    headers = HEADERS.copy()
    status_filter = ' or '.join([f"status eq '{status}'" for status in target_statuses])
    headers['TMV1-Filter'] = status_filter

    # Parameters for fetching and sorting
    params = {
        'orderBy': 'severity desc'
    }

    # Fetch alerts from the API
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error fetching alerts: {response.status_code}, {response.text}")
        return []

    data = response.json()
    alerts = data.get('items', [])

    # Generate real Workbench links
    return [
        {
            'workbench_id': alert.get('id'),
            'workbenchLink': f"https://portal.xdr.trendmicro.com/index.html#/workbench/alerts/{alert.get('id')}", # use URL according to your region
            'model': alert.get('model'),
            'severity': alert.get('severity'),
            'createdDateTime': alert.get('createdDateTime')
        }
        for alert in alerts
    ]

def calculate_time_elapsed(start_time):
    """
    Calculate the elapsed time from the alert's startDateTime to the current time.
    :param start_time: The ISO 8601 string of the alert's startDateTime.
    :return: A human-readable string representing the time elapsed.
    """
    if not start_time:
        return "Unknown"

    # Parse the ISO 8601 datetime string
    alert_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    # Calculate the difference
    elapsed = now - alert_time

    # Convert to human-readable format
    if elapsed.days > 0:
        return f"{elapsed.days} days ago"
    hours = elapsed.seconds // 3600
    if hours > 0:
        return f"{hours} hours ago"
    minutes = (elapsed.seconds // 60) % 60
    return f"{minutes} minutes ago"

def update_data_cache():
    """Periodically fetch data from the API and update the cache."""
    while True:
        try:
            print("Updating data cache...")
            data_cache["new_alerts"] = fetch_alerts_by_status(["Open"])
            data_cache["inprogress_alerts"] = fetch_alerts_by_status(["In Progress"])
            data_cache["closed_alerts"] = fetch_alerts_by_status(["Closed"])
            print("Data cache updated.")
        except Exception as e:
            print(f"Error updating data cache: {e}")
        time.sleep(60)  # Wait for 5 minutes

# Start the background thread to update the data cache
thread = threading.Thread(target=update_data_cache, daemon=True)
thread.start()

if __name__ == '__main__':
    app.run(debug=True)
