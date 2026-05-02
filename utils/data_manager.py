import json
import os
from datetime import date, datetime

# Always store data next to this file, not relative to cwd
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

class DataManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._init_files()

    def _path(self, filename):
        return os.path.join(DATA_DIR, filename)

    def _init_files(self):
        for fname in ["daily_logs.json", "weekly_logs.json", "medications.json",
                      "appointments.json", "settings.json"]:
            p = self._path(fname)
            if not os.path.exists(p):
                with open(p, "w") as f:
                    json.dump({} if fname == "settings.json" else [], f)

    def _load(self, fname):
        with open(self._path(fname)) as f:
            return json.load(f)

    def _save(self, fname, data):
        with open(self._path(fname), "w") as f:
            json.dump(data, f, indent=2, default=str)

    def get_setting(self, key):
        s = self._load("settings.json")
        return s.get(key)

    def save_setting(self, key, value):
        s = self._load("settings.json")
        s[key] = value
        self._save("settings.json", s)

    def save_daily_log(self, log: dict, target_date: str = None):
        logs = self._load("daily_logs.json")
        log["timestamp"] = datetime.now().isoformat()
        save_date = target_date if target_date else str(date.today())
        existing = [l for l in logs if l.get("date") != save_date]
        log["date"] = save_date
        existing.append(log)
        self._save("daily_logs.json", existing)

    def get_daily_logs(self):
        return self._load("daily_logs.json")

    def get_daily_log_for(self, d: str):
        for l in self._load("daily_logs.json"):
            if l.get("date") == d:
                return l
        return None

    def save_weekly_log(self, log: dict):
        logs = self._load("weekly_logs.json")
        week_key = log.get("week")
        existing = [l for l in logs if l.get("week") != week_key]
        log["timestamp"] = datetime.now().isoformat()
        existing.append(log)
        self._save("weekly_logs.json", existing)

    def get_weekly_logs(self):
        return self._load("weekly_logs.json")

    def add_medication(self, med: dict):
        meds = self._load("medications.json")
        med["id"] = datetime.now().isoformat()
        meds.append(med)
        self._save("medications.json", meds)

    def get_medications(self):
        return self._load("medications.json")

    def delete_medication(self, med_id: str):
        meds = [m for m in self._load("medications.json") if m.get("id") != med_id]
        self._save("medications.json", meds)

    def add_appointment(self, appt: dict):
        appts = self._load("appointments.json")
        appt["id"] = datetime.now().isoformat()
        appts.append(appt)
        self._save("appointments.json", appts)

    def get_appointments(self):
        return self._load("appointments.json")

    def delete_appointment(self, appt_id: str):
        appts = [a for a in self._load("appointments.json") if a.get("id") != appt_id]
        self._save("appointments.json", appts)