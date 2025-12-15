# Event Scheduling & Resource Allocation System

A simple Flask web application where organisations can schedule events and allocate shared resources (rooms, instructors, equipment). Includes conflict detection and a utilisation report.

## Features
- CRUD for Events and Resources
- Allocate multiple resources per event
- Conflict detection on create/edit and a dedicated conflicts view
- Utilisation report for a selected date range with upcoming bookings
- Bootstrap UI

## Tech
- Flask, SQLAlchemy, Flask-WTF
- SQLite for local development

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

Visit http://127.0.0.1:5000

## Notes
- Time overlap logic uses `s1 < e2 and s2 < e1`, handling touching intervals as non-overlapping.
- Update `SECRET_KEY` and move to a persistent DB (e.g., MySQL) for production.

## Submission
Add screenshots and a screen-recorded video showing the screens and reports in this README. Then email hr@aerele.in with the subject "Assignment Submission - Event Scheduling & Resource Allocation System".
