import os
import json
import csv
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analysis_tools")
LOG_FILE_JSON = os.path.join(LOG_DIR, "session_logs.json")
LOG_FILE_CSV = os.path.join(LOG_DIR, "session_logs.csv")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def log_session_event(prompt, response, analysis, sanitized_text):
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "prompt": prompt,
        "response": response,
        "sanitized_text": sanitized_text,
        "risk_score": analysis.get("score", 0),
        "classification": analysis.get("classification", "UNKNOWN"),
        "threat_type": analysis.get("threat_type", "None"),
        "patterns_matched": analysis.get("patterns_matched", [])
    }

    # Append to JSON
    logs = []
    if os.path.exists(LOG_FILE_JSON):
        with open(LOG_FILE_JSON, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    logs.append(log_entry)
    with open(LOG_FILE_JSON, "w") as f:
        json.dump(logs, f, indent=4)

    # Append to CSV
    file_exists = os.path.exists(LOG_FILE_CSV)
    with open(LOG_FILE_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=log_entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

def get_session_logs():
    if os.path.exists(LOG_FILE_JSON):
        with open(LOG_FILE_JSON, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []
