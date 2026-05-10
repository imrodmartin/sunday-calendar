#!/usr/bin/env python3
"""
update_schedule.py
Finds the Google Doc named for the upcoming Sunday (e.g. "May 10, 2026"),
parses the Current Happenings section, and updates the schedule in index.html.
Requires env vars: GOOGLE_CREDENTIALS (service account JSON), GOOGLE_DRIVE_FOLDER_ID
"""
import json
import os
import re
from datetime import date, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

DAYS = ["Today", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def next_sunday():
    today = date.today()
    days_ahead = (6 - today.weekday()) % 7 or 7
    return today + timedelta(days=days_ahead)


def build_drive_service():
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)


def find_doc(drive, folder_id, doc_name):
    safe_name = doc_name.replace("'", "\\'")
    results = drive.files().list(
        q=(
            f"name='{safe_name}' and '{folder_id}' in parents"
            " and mimeType='application/vnd.google-apps.document'"
            " and trashed=false"
        ),
        fields="files(id,name)",
    ).execute()
    files = results.get("files", [])
    if not files:
        raise ValueError(f"No Google Doc named '{doc_name}' found in folder '{folder_id}'")
    return files[0]["id"]


def export_as_text(drive, file_id):
    raw = drive.files().export(fileId=file_id, mimeType="text/plain").execute()
    return raw.decode("utf-8")


def parse_happenings(text):
    match = re.search(r"Current Happenings(.*?)(?:\n\s*\n|\Z)", text, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("'Current Happenings' section not found in document")
    section = match.group(1)

    schedule = []
    for day in DAYS:
        day_match = re.search(rf"{day}\s*[-–—]\s*(.*)$", section, re.MULTILINE)
        if not day_match:
            continue
        events_text = day_match.group(1).strip()
        if not events_text:
            continue
        events = [e.strip() for e in re.split(r"\s{2,}", events_text) if e.strip()]
        if events:
            schedule.append((day, events))
    return schedule


def build_schedule_html(schedule):
    rows = []
    for day, events in schedule:
        event_divs = "\n          ".join(f'<div class="event">{e}</div>' for e in events)
        rows.append(
            f'      <div class="schedule-row">\n'
            f'        <div class="day">{day}</div>\n'
            f'        <div class="events">\n'
            f'          {event_divs}\n'
            f'        </div>\n'
            f'      </div>'
        )
    return "\n\n".join(rows)


def update_html(schedule_html, html_path="index.html"):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(
        r"<!-- SCHEDULE_START -->.*?<!-- SCHEDULE_END -->",
        f"<!-- SCHEDULE_START -->\n{schedule_html}\n<!-- SCHEDULE_END -->",
        content,
        flags=re.DOTALL,
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    sunday = next_sunday()
    doc_name = f"{sunday.strftime('%B')} {sunday.day}, {sunday.year}"
    print(f"Looking for doc: '{doc_name}'")

    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]
    drive = build_drive_service()

    file_id = find_doc(drive, folder_id, doc_name)
    print(f"Found doc ID: {file_id}")

    text = export_as_text(drive, file_id)
    schedule = parse_happenings(text)
    print(f"Parsed {len(schedule)} schedule rows: {[d for d, _ in schedule]}")

    schedule_html = build_schedule_html(schedule)
    update_html(schedule_html)
    print("Updated index.html")
