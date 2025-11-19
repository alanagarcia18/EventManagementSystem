# EventManagementSystem

A small demo Event Management System using Python, SQLite, and Tkinter.

Run instructions:

1. Ensure you have Python 3 installed (3.8+ recommended).
2. From this repository folder run:

```bash
python main.py
```

The app will create an `events.db` SQLite file in the project directory and seed sample users, venues, and events. Use the top "User" combobox to login (or create a new user). Organizer and Admin roles unlock additional panels.

Features:
- Browse and search events
- Register for events as an attendee (capacity enforced)
- Organizer panel: create events
- Admin panel: manage users and venues

Notes:
- This is a simple demo intended as a starting point. Improvements: better validation, date/time pickers, edit/delete events, and persistence prompts.
