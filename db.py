import sqlite3
import os
from datetime import datetime


class DB:
    def __init__(self, path=None):
        self.path = path or os.path.join(os.path.dirname(__file__), 'events.db')
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, role TEXT
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY, name TEXT, address TEXT, capacity INTEGER
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY, title TEXT, description TEXT, venue_id INTEGER,
            organizer_id INTEGER, capacity INTEGER
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY, event_id INTEGER, start TEXT, end TEXT
        )
        ''')
        cur.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY, event_id INTEGER, user_id INTEGER, created_at TEXT
        )
        ''')
        self.conn.commit()
        # seed sample data if users empty
        cur.execute('SELECT count(*) FROM users')
        if cur.fetchone()[0] == 0:
            self._seed(cur)
            self.conn.commit()

    def _seed(self, cur):
        # users
        cur.execute("INSERT INTO users (name,email,role) VALUES (?,?,?)", ('Admin User','admin@example.com','admin'))
        cur.execute("INSERT INTO users (name,email,role) VALUES (?,?,?)", ('Organizer One','org1@example.com','organizer'))
        cur.execute("INSERT INTO users (name,email,role) VALUES (?,?,?)", ('Attendee One','att1@example.com','attendee'))
        # venues
        cur.execute("INSERT INTO venues (name,address,capacity) VALUES (?,?,?)", ('Main Hall','123 Main St',200))
        cur.execute("INSERT INTO venues (name,address,capacity) VALUES (?,?,?)", ('Room A','45 Side Rd',50))
        # events
        cur.execute("INSERT INTO events (title,description,venue_id,organizer_id,capacity) VALUES (?,?,?,?,?)",
                    ('Community Meetup','A friendly meetup','1','2',100))
        cur.execute("INSERT INTO events (title,description,venue_id,organizer_id,capacity) VALUES (?,?,?,?,?)",
                    ('Workshop','Skill-building workshop','2','2',30))
        # schedules
        cur.execute("INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)", (1,'2025-11-20 18:00','2025-11-20 20:00'))
        cur.execute("INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)", (2,'2025-11-22 09:00','2025-11-22 12:00'))

    # Users
    def get_users(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,email,role FROM users ORDER BY id')
        return cur.fetchall()

    def get_user_by_email(self, email):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,email,role FROM users WHERE email=?', (email,))
        r = cur.fetchone()
        return tuple(r) if r else None

    def create_user(self, name, email, role='attendee'):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO users (name,email,role) VALUES (?,?,?)', (name, email, role))
        self.conn.commit()
        return cur.lastrowid

    def delete_user(self, user_id):
        cur = self.conn.cursor()
        cur.execute('DELETE FROM users WHERE id=?', (user_id,))
        self.conn.commit()

    # Venues
    def create_venue(self, name, address, capacity):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO venues (name,address,capacity) VALUES (?,?,?)', (name, address, capacity))
        self.conn.commit()
        return cur.lastrowid

    def get_venues(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,address,capacity FROM venues ORDER BY id')
        return cur.fetchall()

    # Events & schedules
    def create_event(self, title, description, venue_id, organizer_id, capacity, start=None, end=None):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO events (title,description,venue_id,organizer_id,capacity) VALUES (?,?,?,?,?)',
                    (title, description, venue_id, organizer_id, capacity))
        eid = cur.lastrowid
        if start:
            cur.execute('INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)', (eid, start, end))
        self.conn.commit()
        return eid

    def get_events(self):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity, v.name as venue_name, s.start
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        ORDER BY s.start IS NULL, s.start
        ''')
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def search_events(self, q):
        cur = self.conn.cursor()
        qlike = f"%{q}%"
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity, v.name as venue_name, s.start
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        WHERE e.title LIKE ? OR e.description LIKE ? OR v.name LIKE ?
        ORDER BY s.start IS NULL, s.start
        ''', (qlike, qlike, qlike))
        return [dict(r) for r in cur.fetchall()]

    def get_event(self, event_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity, v.name as venue_name, s.start
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        WHERE e.id=?
        ''', (event_id,))
        r = cur.fetchone()
        return dict(r) if r else None

    def get_event_attendees(self, event_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT u.id,u.name,u.email
        FROM registrations r
        JOIN users u ON u.id=r.user_id
        WHERE r.event_id=?
        ''', (event_id,))
        return [dict(r) for r in cur.fetchall()]

    def register_user_for_event(self, user_id, event_id):
        cur = self.conn.cursor()
        # check duplicate
        cur.execute('SELECT count(*) FROM registrations WHERE user_id=? AND event_id=?', (user_id, event_id))
        if cur.fetchone()[0] > 0:
            raise Exception('Already registered')
        # check capacity
        cur.execute('SELECT capacity FROM events WHERE id=?', (event_id,))
        row = cur.fetchone()
        if not row:
            raise Exception('Event not found')
        cap = row[0]
        cur.execute('SELECT count(*) FROM registrations WHERE event_id=?', (event_id,))
        regcount = cur.fetchone()[0]
        if cap is not None and regcount >= cap:
            raise Exception('Event is full')
        cur.execute('INSERT INTO registrations (event_id,user_id,created_at) VALUES (?,?,?)',
                    (event_id, user_id, datetime.utcnow().isoformat()))
        self.conn.commit()
        return cur.lastrowid

    def get_registrations_by_user(self, user_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT r.event_id, e.title, s.start, v.name as venue_name
        FROM registrations r
        JOIN events e ON e.id=r.event_id
        LEFT JOIN schedules s ON s.event_id=e.id
        LEFT JOIN venues v ON v.id=e.venue_id
        WHERE r.user_id=?
        ''', (user_id,))
        return [dict(r) for r in cur.fetchall()]

    def get_events_by_organizer(self, org_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity, v.name as venue_name, s.start
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        WHERE e.organizer_id=?
        ''', (org_id,))
        return [dict(r) for r in cur.fetchall()]
