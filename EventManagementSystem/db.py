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
            id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, role TEXT, password_hash TEXT
        )
        ''')
        
        # Add password_hash column if it doesn't exist (for existing databases)
        cur.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cur.fetchall()]
        if 'password_hash' not in columns:
            cur.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
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
        from werkzeug.security import generate_password_hash
        # users with default passwords
        cur.execute("INSERT INTO users (name,email,role,password_hash) VALUES (?,?,?,?)", 
                   ('Admin User','admin@eventmanager.com','admin', generate_password_hash('admin123')))
        cur.execute("INSERT INTO users (name,email,role,password_hash) VALUES (?,?,?,?)", 
                   ('Event Organizer','organizer@eventmanager.com','organizer', generate_password_hash('organizer123')))
        cur.execute("INSERT INTO users (name,email,role,password_hash) VALUES (?,?,?,?)", 
                   ('John Attendee','user@eventmanager.com','attendee', generate_password_hash('user123')))
        # venues
        cur.execute("INSERT INTO venues (name,address,capacity) VALUES (?,?,?)", ('Main Hall','123 Main St',200))
        cur.execute("INSERT INTO venues (name,address,capacity) VALUES (?,?,?)", ('Room A','45 Side Rd',50))
        cur.execute("INSERT INTO venues (name,address,capacity) VALUES (?,?,?)", ('Conference Center','789 Business Ave',500))
        # events
        cur.execute("INSERT INTO events (title,description,venue_id,organizer_id,capacity) VALUES (?,?,?,?,?)",
                    ('Community Meetup','A friendly meetup for the community','1','2',100))
        cur.execute("INSERT INTO events (title,description,venue_id,organizer_id,capacity) VALUES (?,?,?,?,?)",
                    ('Tech Workshop','Skill-building workshop on latest technologies','2','2',30))
        cur.execute("INSERT INTO events (title,description,venue_id,organizer_id,capacity) VALUES (?,?,?,?,?)",
                    ('Annual Conference','Our biggest event of the year','3','1',400))
        # schedules
        cur.execute("INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)", (1,'2025-11-25 18:00','2025-11-25 20:00'))
        cur.execute("INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)", (2,'2025-11-27 09:00','2025-11-27 12:00'))
        cur.execute("INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)", (3,'2025-12-05 09:00','2025-12-05 17:00'))

    # Users
    def get_users(self):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,email,role FROM users ORDER BY id')
        return cur.fetchall()

    def get_user_by_email(self, email):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,email,role,password_hash FROM users WHERE email=?', (email,))
        r = cur.fetchone()
        return tuple(r) if r else None

    def get_user_by_id(self, user_id):
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,email,role,password_hash FROM users WHERE id=?', (user_id,))
        r = cur.fetchone()
        return tuple(r) if r else None

    def create_user_with_password(self, name, email, role='attendee', password_hash=None):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO users (name,email,role,password_hash) VALUES (?,?,?,?)', (name, email, role, password_hash))
        self.conn.commit()
        return cur.lastrowid

    def create_user(self, name, email, role='attendee'):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO users (name,email,role) VALUES (?,?,?)', (name, email, role))
        self.conn.commit()
        return cur.lastrowid

    def delete_user(self, user_id):
        cur = self.conn.cursor()
        # Delete registrations first
        cur.execute('DELETE FROM registrations WHERE user_id=?', (user_id,))
        # Then delete user
        cur.execute('DELETE FROM users WHERE id=?', (user_id,))
        self.conn.commit()

    def update_user_role(self, user_id, new_role):
        """Update a user's role"""
        cur = self.conn.cursor()
        cur.execute('UPDATE users SET role=? WHERE id=?', (new_role, user_id))
        self.conn.commit()
        return cur.rowcount > 0

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

    def get_venue(self, venue_id):
        """Get a single venue by ID"""
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,address,capacity FROM venues WHERE id=?', (venue_id,))
        return cur.fetchone()

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
        SELECT e.id,e.title,e.description,e.capacity,e.organizer_id, v.name as venue_name, v.address as venue_address, s.start, s.end, u.name as organizer_name, u.email as organizer_email
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        LEFT JOIN users u ON e.organizer_id=u.id
        ORDER BY s.start IS NULL, s.start
        ''')
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def search_events(self, q):
        cur = self.conn.cursor()
        qlike = f"%{q}%"
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity,e.organizer_id, v.name as venue_name, v.address as venue_address, s.start, s.end, u.name as organizer_name, u.email as organizer_email
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        LEFT JOIN users u ON e.organizer_id=u.id
        WHERE e.title LIKE ? OR e.description LIKE ? OR v.name LIKE ?
        ORDER BY s.start IS NULL, s.start
        ''', (qlike, qlike, qlike))
        return [dict(r) for r in cur.fetchall()]

    def get_event(self, event_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity,e.organizer_id, v.name as venue_name, v.address as venue_address, s.start, s.end, u.name as organizer_name, u.email as organizer_email
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        LEFT JOIN users u ON e.organizer_id=u.id
        WHERE e.id=?
        ''', (event_id,))
        r = cur.fetchone()
        return dict(r) if r else None

    def get_event_attendees(self, event_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT u.id,u.name,u.email,u.role, r.created_at as registration_date
        FROM registrations r
        JOIN users u ON u.id=r.user_id
        WHERE r.event_id=?
        ORDER BY r.created_at
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

    def unregister_user_from_event(self, user_id, event_id):
        """Remove a user's registration from an event"""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM registrations WHERE user_id=? AND event_id=?', (user_id, event_id))
        self.conn.commit()
        return cur.rowcount > 0

    def get_registrations_by_user(self, user_id):
        cur = self.conn.cursor()
        cur.execute('''
        SELECT r.event_id, e.title as event_title, e.description, e.capacity, s.start, s.end, v.name as venue_name, v.address as venue_address, u.name as organizer_name, u.email as organizer_email, r.created_at as registration_date
        FROM registrations r
        JOIN events e ON e.id=r.event_id
        LEFT JOIN schedules s ON s.event_id=e.id
        LEFT JOIN venues v ON v.id=e.venue_id
        LEFT JOIN users u ON u.id=e.organizer_id
        WHERE r.user_id=?
        ORDER BY s.start IS NULL, s.start
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
        ORDER BY s.start IS NULL, s.start
        ''', (org_id,))
        return [dict(r) for r in cur.fetchall()]

    def check_venue_availability(self, venue_id, start_time, end_time, exclude_event_id=None):
        """
        Check if a venue is available for the specified time slot.
        Returns True if available, False if there's a conflict.
        """
        cur = self.conn.cursor()
        
        # Check for overlapping events at the same venue
        query = '''
        SELECT COUNT(*) FROM events e
        JOIN schedules s ON e.id = s.event_id
        WHERE e.venue_id = ? 
        AND ((s.start <= ? AND s.end > ?) OR 
             (s.start < ? AND s.end >= ?) OR
             (s.start >= ? AND s.end <= ?))
        '''
        params = [venue_id, start_time, start_time, end_time, end_time, start_time, end_time]
        
        # Exclude current event if updating
        if exclude_event_id:
            query += ' AND e.id != ?'
            params.append(exclude_event_id)
            
        cur.execute(query, params)
        conflict_count = cur.fetchone()[0]
        
        return conflict_count == 0
    
    def update_event(self, event_id, title, description, venue_id, capacity, start=None, end=None):
        """Update an existing event"""
        cur = self.conn.cursor()
        cur.execute('''UPDATE events 
                      SET title=?, description=?, venue_id=?, capacity=? 
                      WHERE id=?''', 
                   (title, description, venue_id, capacity, event_id))
        
        # Update schedule if provided
        if start:
            cur.execute('DELETE FROM schedules WHERE event_id=?', (event_id,))
            cur.execute('INSERT INTO schedules (event_id,start,end) VALUES (?,?,?)', 
                       (event_id, start, end))
        
        self.conn.commit()
        return cur.rowcount > 0

    def delete_event(self, event_id):
        """Delete an event and all related data"""
        cur = self.conn.cursor()
        # Delete in order: registrations, schedules, then event
        cur.execute('DELETE FROM registrations WHERE event_id=?', (event_id,))
        cur.execute('DELETE FROM schedules WHERE event_id=?', (event_id,))
        cur.execute('DELETE FROM events WHERE id=?', (event_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def remove_user_from_event(self, user_id, event_id):
        """Remove a specific user's registration from an event (for organizers/admins)"""
        cur = self.conn.cursor()
        cur.execute('DELETE FROM registrations WHERE user_id=? AND event_id=?', 
                   (user_id, event_id))
        self.conn.commit()
        return cur.rowcount > 0

    def get_event_with_organizer(self, event_id):
        """Get event details including organizer info"""
        cur = self.conn.cursor()
        cur.execute('''
        SELECT e.id, e.title, e.description, e.capacity, e.organizer_id,
               v.name as venue_name, v.address as venue_address, v.id as venue_id,
               s.start, s.end,
               u.name as organizer_name
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        LEFT JOIN users u ON u.id=e.organizer_id
        WHERE e.id=?
        ''', (event_id,))
        r = cur.fetchone()
        return dict(r) if r else None

    def get_active_events(self):
        """Get only events that haven't ended yet"""
        from datetime import datetime
        cur = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity, v.name as venue_name, s.start, s.end
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        WHERE s.end IS NULL OR s.end > ?
        ORDER BY s.start IS NULL, s.start
        ''', (now,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def search_active_events(self, q):
        """Search only active events"""
        from datetime import datetime
        cur = self.conn.cursor()
        now = datetime.now().isoformat()
        qlike = f"%{q}%"
        
        cur.execute('''
        SELECT e.id,e.title,e.description,e.capacity, v.name as venue_name, s.start, s.end
        FROM events e
        LEFT JOIN venues v ON e.venue_id=v.id
        LEFT JOIN schedules s ON s.event_id=e.id
        WHERE (s.end IS NULL OR s.end > ?) 
        AND (e.title LIKE ? OR e.description LIKE ? OR v.name LIKE ?)
        ORDER BY s.start IS NULL, s.start
        ''', (now, qlike, qlike, qlike))
        return [dict(r) for r in cur.fetchall()]

    def get_all_users(self):
        """Get all users with password hash info"""
        cur = self.conn.cursor()
        cur.execute('SELECT id,name,email,role,password_hash FROM users ORDER BY id')
        return cur.fetchall()

    def get_event_statistics(self):
        """Get basic statistics about the system"""
        cur = self.conn.cursor()
        
        # Total events
        cur.execute('SELECT COUNT(*) FROM events')
        total_events = cur.fetchone()[0]
        
        # Total users
        cur.execute('SELECT COUNT(*) FROM users')
        total_users = cur.fetchone()[0]
        
        # Total venues
        cur.execute('SELECT COUNT(*) FROM venues')
        total_venues = cur.fetchone()[0]
        
        # Total registrations
        cur.execute('SELECT COUNT(*) FROM registrations')
        total_registrations = cur.fetchone()[0]
        
        # User role counts
        cur.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('attendee',))
        attendee_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('organizer',))
        organizer_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
        admin_count = cur.fetchone()[0]
        
        # Events with registrations
        cur.execute('SELECT COUNT(DISTINCT event_id) FROM registrations')
        events_with_registrations = cur.fetchone()[0]
        
        return {
            'total_events': total_events,
            'total_users': total_users,
            'total_venues': total_venues,
            'total_registrations': total_registrations,
            'attendee_count': attendee_count,
            'organizer_count': organizer_count,
            'admin_count': admin_count,
            'events_with_registrations': events_with_registrations
        }
