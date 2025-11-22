from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from db import DB
from datetime import datetime, timedelta
import re
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Initialize database
db = DB()

@app.route('/')
def landing():
    """Beautiful landing page"""
    return render_template('landing.html')

@app.route('/about')
def about():
    """About page"""
    stats = db.get_event_statistics()
    return render_template('about.html', stats=stats)

@app.route('/creator')
def creator():
    """Creator/Developer page"""
    return render_template('creator.html')

@app.route('/login-page')
def login_page():
    """Login page with mandatory authentication"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle login"""
    from werkzeug.security import check_password_hash
    
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email:
        flash('Please enter your email address', 'error')
        return redirect(url_for('login_page'))
    
    user = db.get_user_by_email(email)
    if not user:
        flash('User not found. Please create an account first.', 'error')
        return redirect(url_for('login_page'))
    
    # Check password if password_hash exists
    if len(user) > 4 and user[4] and not check_password_hash(user[4], password):
        flash('Invalid password. Please try again.', 'error')
        return redirect(url_for('login_page'))
    
    # Store user in session
    session['user_id'] = user[0]
    session['user_name'] = user[1]
    session['user_email'] = user[2]
    session['user_role'] = user[3]
    
    flash(f'Welcome back, {user[1]}!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('landing'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'attendee').strip()
    
    # Validation
    if not name or not email or not password:
        flash('Name, email, and password are required', 'error')
        return render_template('register.html')
    
    # Password validation
    if len(password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return render_template('register.html')
    
    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        flash('Please enter a valid email address', 'error')
        return render_template('register.html')
    
    try:
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(password)
        db.create_user_with_password(name, email, role, password_hash)
        flash(f'Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login_page'))
    except Exception as e:
        flash(f'Error creating account: {str(e)}', 'error')
        return render_template('register.html')

def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to require specific role"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'error')
                return redirect(url_for('login_page'))
            if session.get('user_role') != required_role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - redirects admins to admin panel"""
    # Redirect admins to admin panel
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_panel'))
    
    # Get some stats for the dashboard
    events = db.get_events()
    user_registrations = db.get_registrations_by_user(session['user_id'])
    
    # Get events organized by current user if they're an organizer
    organized_events = []
    if session.get('user_role') == 'organizer':
        organized_events = db.get_events_by_organizer(session['user_id'])
    
    return render_template('dashboard.html', 
                         events=events[:6],  # Show only first 6 events
                         user_registrations=user_registrations[:5],  # Show only first 5 registrations
                         organized_events=organized_events[:5])

@app.route('/events')
@login_required
def events():
    """Browse all events - excludes events user organizes"""
    search = request.args.get('search', '').strip()
    all_events = db.search_events(search) if search else db.get_events()
    
    # Filter out events where current user is the organizer
    events = [event for event in all_events if event['organizer_id'] != session['user_id']]
    
    # Add registration count for each event
    for event in events:
        event['registered_count'] = len(db.get_event_attendees(event['id']))
        event['is_full'] = event['registered_count'] >= event['capacity']
        event['is_registered'] = any(reg['event_id'] == event['id'] 
                                   for reg in db.get_registrations_by_user(session['user_id']))
    
    return render_template('events.html', events=events, search=search)

@app.route('/event/<int:event_id>')
@login_required
def event_detail(event_id):
    """Event details page"""
    event = db.get_event_with_organizer(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events'))
    
    attendees = db.get_event_attendees(event_id)
    is_registered = any(reg['event_id'] == event_id 
                       for reg in db.get_registrations_by_user(session['user_id']))
    
    return render_template('event_detail.html', 
                         event=event, 
                         attendees=attendees, 
                         is_registered=is_registered,
                         registered_count=len(attendees))

@app.route('/register_event/<int:event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    """Register for an event - admins and organizers of the event cannot register"""
    # Prevent admins from registering for events
    if session.get('user_role') == 'admin':
        flash('Administrators cannot register for events. Only attendees and organizers can register.', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Check if user is the organizer of this event
    event = db.get_event_with_organizer(event_id)
    if event and event['organizer_id'] == session['user_id']:
        flash('You cannot register for your own event as the organizer.', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
    
    try:
        db.register_user_for_event(session['user_id'], event_id)
        flash('Successfully registered for the event!', 'success')
    except Exception as e:
        flash(f'Registration failed: {str(e)}', 'error')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/unregister_event/<int:event_id>', methods=['POST'])
@login_required
def unregister_event(event_id):
    """Unregister from an event"""
    try:
        db.unregister_user_from_event(session['user_id'], event_id)
        flash('Successfully unregistered from the event', 'info')
    except Exception as e:
        flash(f'Unregistration failed: {str(e)}', 'error')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/my-registrations')
@login_required
def my_registrations():
    """User's registrations"""
    registrations = db.get_registrations_by_user(session['user_id'])
    
    # Add status to each registration
    for reg in registrations:
        if reg.get('start'):
            try:
                start_dt = datetime.fromisoformat(reg['start'].replace('T', ' '))
                now = datetime.now()
                if start_dt < now:
                    reg['status'] = 'past'
                elif start_dt - now < timedelta(days=1):
                    reg['status'] = 'soon'
                else:
                    reg['status'] = 'upcoming'
            except:
                reg['status'] = 'unknown'
        else:
            reg['status'] = 'tbd'
    
    return render_template('my_registrations.html', registrations=registrations)

@app.route('/organizer')
@login_required
def organizer_panel():
    """
    Organizer panel - Available to any user who creates events
    Shows user's created events and management tools
    Connected to: Dashboard (navigation), Create Event (event creation), Event management
    """
    events = db.get_events_by_organizer(session['user_id'])
    
    # Add stats to each event - inline comments for functionality
    for event in events:
        attendees = db.get_event_attendees(event['id'])  # Get all registered users
        event['registered_count'] = len(attendees)       # Count registrations
        event['attendees'] = attendees                   # Store attendee data for management
    
    return render_template('organizer.html', events=events)

@app.route('/my-events')  # Alternative route for clarity
@login_required
def my_events_redirect():
    """Alternative route that redirects to organizer panel"""
    return redirect(url_for('organizer_panel'))

@app.route('/my_events')
@login_required
def my_events():
    """User's created events (if they've created any)"""
    created_events = db.get_events_by_organizer(session['user_id'])
    
    # Add stats to each event
    for event in created_events:
        attendees = db.get_event_attendees(event['id'])
        event['registered_count'] = len(attendees)
        event['attendees'] = attendees
    
    return render_template('my_events.html', events=created_events)

@app.route('/create-event', methods=['GET', 'POST'])
@login_required
def create_event():
    """
    Create new event - Available to attendees and organizers only
    Admins cannot create events
    When a user creates an event, they become its organizer
    Connected to: Organizer panel (management), Dashboard (navigation)
    """
    # Prevent admins from creating events
    if session.get('user_role') == 'admin':
        flash('Administrators cannot create events. Only attendees and organizers can create events.', 'error')
        return redirect(url_for('admin_panel'))
    
    if request.method == 'GET':
        venues = db.get_venues()  # Get all available venues
        return render_template('create_event.html', venues=venues)
    
    # Form data extraction with validation
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    venue_id = request.form.get('venue_id')
    capacity = request.form.get('capacity', '').strip()
    start_date = request.form.get('start_date', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_date = request.form.get('end_date', '').strip()
    end_time = request.form.get('end_time', '').strip()
    
    # Validation
    if not all([title, venue_id, capacity, start_date, start_time]):
        flash('Please fill in all required fields', 'error')
        venues = db.get_venues()
        return render_template('create_event.html', venues=venues)
    
    try:
        capacity = int(capacity)
        venue_id = int(venue_id)
    except ValueError:
        flash('Please enter valid numbers for capacity and venue', 'error')
        venues = db.get_venues()
        return render_template('create_event.html', venues=venues)
    
    # Combine date and time
    start_datetime = f"{start_date} {start_time}"
    end_datetime = None
    if end_date and end_time:
        end_datetime = f"{end_date} {end_time}"
    
    # Validate datetime format
    try:
        datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
        if end_datetime:
            datetime.strptime(end_datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        flash('Please enter valid date and time formats', 'error')
        venues = db.get_venues()
        return render_template('create_event.html', venues=venues)
    
    # Check venue availability for the requested time slot
    end_check = end_datetime if end_datetime else start_datetime
    if not db.check_venue_availability(venue_id, start_datetime, end_check):
        flash('This venue is already booked for the selected date and time. Please choose a different time or venue.', 'error')
        venues = db.get_venues()
        return render_template('create_event.html', venues=venues)
    
    try:
        event_id = db.create_event(title, description, venue_id, session['user_id'], 
                       capacity, start_datetime, end_datetime)
        
        # Update user role to organizer if they created an event and aren't admin
        if session.get('user_role') == 'attendee':
            db.update_user_role(session['user_id'], 'organizer')
            session['user_role'] = 'organizer'
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('my_events'))
    except Exception as e:
        flash(f'Error creating event: {str(e)}', 'error')
        venues = db.get_venues()
        return render_template('create_event.html', venues=venues)

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    """Edit an event (only by event creator or admin)"""
    event = db.get_event_with_organizer(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events'))
    
    # Check if user can edit (event creator or admin)
    if event['organizer_id'] != session['user_id'] and session['user_role'] != 'admin':
        flash('You can only edit events you created', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
    
    if request.method == 'GET':
        venues = db.get_venues()
        return render_template('edit_event.html', event=event, venues=venues)
    
    # Handle POST request
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    venue_id = request.form.get('venue_id')
    capacity = request.form.get('capacity', '').strip()
    start_date = request.form.get('start_date', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_date = request.form.get('end_date', '').strip()
    end_time = request.form.get('end_time', '').strip()
    
    # Validation
    if not all([title, venue_id, capacity, start_date, start_time]):
        flash('Please fill in all required fields', 'error')
        venues = db.get_venues()
        return render_template('edit_event.html', event=event, venues=venues)
    
    try:
        capacity = int(capacity)
        venue_id = int(venue_id)
    except ValueError:
        flash('Please enter valid numbers for capacity and venue', 'error')
        venues = db.get_venues()
        return render_template('edit_event.html', event=event, venues=venues)
    
    # Combine date and time
    start_datetime = f"{start_date} {start_time}"
    end_datetime = None
    if end_date and end_time:
        end_datetime = f"{end_date} {end_time}"
    
    try:
        db.update_event(event_id, title, description, venue_id, capacity, 
                       start_datetime, end_datetime)
        flash('Event updated successfully!', 'success')
        return redirect(url_for('event_detail', event_id=event_id))
    except Exception as e:
        flash(f'Error updating event: {str(e)}', 'error')
        venues = db.get_venues()
        return render_template('edit_event.html', event=event, venues=venues)

@app.route('/manage_event/<int:event_id>')
@login_required
def manage_event(event_id):
    """Event management page with options to edit, remove attendees, or delete"""
    event = db.get_event_with_organizer(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('my_events'))
    
    # Check if user can manage (event creator or admin)
    if event['organizer_id'] != session['user_id'] and session['user_role'] != 'admin':
        flash('You can only manage events you created', 'error')
        return redirect(url_for('events'))
    
    # Get event attendees
    attendees = db.get_event_attendees(event_id)
    registered_count = len(attendees)
    
    # Get venue information if available
    venue = None
    if event['venue_id']:
        venue = db.get_venue(event['venue_id'])
    
    return render_template('manage_event.html', 
                         event=event, 
                         attendees=attendees,
                         registered_count=registered_count,
                         venue=venue)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete an event (only by event creator or admin)"""
    event = db.get_event_with_organizer(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events'))
    
    # Check if user can delete (event creator or admin)
    if event['organizer_id'] != session['user_id'] and session['user_role'] != 'admin':
        flash('You can only delete events you created', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
    
    try:
        db.delete_event(event_id)
        flash('Event deleted successfully', 'success')
        return redirect(url_for('my_events'))
    except Exception as e:
        flash(f'Error deleting event: {str(e)}', 'error')
        return redirect(url_for('event_detail', event_id=event_id))

@app.route('/remove_attendee/<int:event_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_attendee(event_id, user_id):
    """Remove an attendee from an event (only by event creator or admin)"""
    event = db.get_event_with_organizer(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('events'))
    
    # Check if user can remove attendees (event creator or admin)
    if event['organizer_id'] != session['user_id'] and session['user_role'] != 'admin':
        flash('You can only manage attendees for events you created', 'error')
        return redirect(url_for('event_detail', event_id=event_id))
    
    try:
        db.remove_user_from_event(user_id, event_id)
        flash('Attendee removed successfully', 'success')
    except Exception as e:
        flash(f'Error removing attendee: {str(e)}', 'error')
    
    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/admin')
@role_required('admin')
def admin_panel():
    """Admin panel"""
    stats = db.get_event_statistics()
    events = db.get_events()
    
    # Add registration count to each event for display
    for event in events:
        event['registered_count'] = len(db.get_event_attendees(event['id']))
    
    return render_template('admin.html', stats=stats, events=events)

@app.route('/admin/events')
@role_required('admin')
def admin_events():
    """Admin event management - dedicated events page"""
    events = db.get_events()
    
    # Add registration count to each event for display
    for event in events:
        event['registered_count'] = len(db.get_event_attendees(event['id']))
    
    return render_template('admin_events.html', events=events)

@app.route('/admin/event/<int:event_id>')
@role_required('admin')
def admin_event_detail(event_id):
    """Admin-specific detailed event view with complete information"""
    event = db.get_event_with_organizer(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('admin_events'))
    
    # Get attendees with their information
    attendees = db.get_event_attendees(event_id)
    
    # Get venue information if exists
    venue = None
    if event.get('venue_id'):
        venues = db.get_venues()
        venue = next((v for v in venues if v[0] == event['venue_id']), None)
    
    return render_template('admin_event_detail.html', 
                         event=event, 
                         attendees=attendees, 
                         venue=venue,
                         registered_count=len(attendees))

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    """Manage users"""
    users = db.get_users()
    return render_template('admin_users.html', users=users)

@app.route('/admin/venues')
@role_required('admin')
def admin_venues():
    """Manage venues"""
    venues = db.get_venues()
    return render_template('admin_venues.html', venues=venues)

@app.route('/admin/create-venue', methods=['POST'])
@role_required('admin')
def create_venue():
    """Create new venue"""
    name = request.form.get('name', '').strip()
    address = request.form.get('address', '').strip()
    capacity = request.form.get('capacity', '').strip()
    
    if not all([name, address, capacity]):
        flash('All fields are required', 'error')
        return redirect(url_for('admin_venues'))
    
    try:
        capacity = int(capacity)
        db.create_venue(name, address, capacity)
        flash(f'Venue "{name}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating venue: {str(e)}', 'error')
    
    return redirect(url_for('admin_venues'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    """Delete user"""
    if user_id == session['user_id']:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        db.delete_user(user_id)
        flash('User deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_event/<int:event_id>', methods=['POST'])
@role_required('admin')
def admin_delete_event(event_id):
    """
    Admin endpoint to delete events
    Removes event and all associated registrations and schedules
    """
    try:
        event = db.get_event(event_id)
        if not event:
            flash('Event not found.', 'error')
            return redirect(url_for('admin_panel'))
        
        event_title = event['title']
        if db.delete_event(event_id):
            flash(f'Event "{event_title}" deleted successfully.', 'success')
        else:
            flash('Failed to delete event.', 'error')
    except Exception as e:
        flash(f'Error deleting event: {str(e)}', 'error')
    
    return redirect(url_for('admin_panel'))

# AI Chat Feature
@app.route('/api/chat', methods=['POST'])
@login_required
def chat_with_ai():
    """AI Chat feature using a simple response generator"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generate AI response
        ai_response = generate_ai_response(user_message)
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_ai_response(message):
    """Generate AI-like responses for event management"""
    message_lower = message.lower()
    
    # Event creation and planning
    if any(word in message_lower for word in ['create event', 'new event', 'organize', 'plan event']):
        return "🎉 **Creating an Event?** Here's your step-by-step guide:\n\n1. **Choose a compelling title** - Make it clear and exciting!\n2. **Select the perfect venue** - Consider capacity, location, and accessibility\n3. **Set the right date/time** - Check for conflicts and your audience's availability\n4. **Write a detailed description** - Help people understand what to expect\n5. **Set appropriate capacity** - Better to start smaller and expand if needed\n\n💡 **Pro tip**: Events with clear descriptions get 3x more registrations!"
    
    elif any(word in message_lower for word in ['venue', 'location', 'place', 'where']):
        return "📍 **Choosing the Perfect Venue:**\n\n🏢 **Consider these factors:**\n• **Capacity** - Room for everyone comfortably\n• **Accessibility** - Easy to reach by car/public transport\n• **Parking** - Adequate space for attendees\n• **Facilities** - Audio/visual equipment, restrooms, catering\n• **Atmosphere** - Matches your event type\n\n🎯 **Popular venue types:** Conference rooms for workshops, outdoor spaces for networking, auditoriums for presentations. What type of event are you planning?"
    
    elif any(word in message_lower for word in ['register', 'join', 'attend', 'sign up']):
        return "✨ **Want to Join Events?** Here's how:\n\n1. **Browse Events** - Check out what's available\n2. **Read descriptions** - Make sure it's right for you\n3. **Check the date** - Mark your calendar\n4. **Register early** - Popular events fill up fast!\n5. **Get reminders** - We'll notify you before the event\n\n🎟️ **Registration is free and easy!** What kind of events interest you most?"
    
    elif any(word in message_lower for word in ['time', 'when', 'schedule', 'timing']):
        return "⏰ **Perfect Event Timing:**\n\n🗓️ **Best times by event type:**\n• **Workshops**: Weekday mornings (9-11 AM)\n• **Networking**: Weekday evenings (6-8 PM)\n• **Social events**: Weekend afternoons\n• **Conferences**: Full weekdays\n\n📅 **Avoid conflicts with:**\n• Major holidays\n• Local big events\n• Exam periods (if targeting students)\n\n🎯 **Pro tip**: Send save-the-dates 2-4 weeks in advance!"
    
    elif any(word in message_lower for word in ['capacity', 'how many', 'size', 'attendees']):
        return "👥 **Setting Event Capacity:**\n\n📊 **Guidelines by event type:**\n• **Intimate workshops**: 10-25 people\n• **Team meetings**: 5-15 people\n• **Networking events**: 30-100 people\n• **Large conferences**: 100+ people\n\n💡 **Smart strategy:**\n1. Start with 80% of venue capacity\n2. Account for no-shows (usually 10-20%)\n3. Leave room for last-minute additions\n\n🎯 **Better to have engaged attendees than empty seats!**"
    
    elif any(word in message_lower for word in ['manage', 'organizer', 'host', 'run event']):
        return "🎪 **Event Management Pro Tips:**\n\n📋 **Before the event:**\n• Send reminder emails 1 week & 1 day before\n• Prepare attendee list and materials\n• Test all equipment\n\n🎯 **During the event:**\n• Arrive 30 mins early\n• Welcome attendees personally\n• Keep to your schedule\n• Encourage networking\n\n✅ **After the event:**\n• Send thank you emails\n• Gather feedback\n• Plan your next event!\n\nNeed help with any specific aspect?"
    
    elif any(word in message_lower for word in ['network', 'meet people', 'connections']):
        return "🤝 **Networking Like a Pro:**\n\n🌟 **At events, try this:**\n1. **Arrive early** - Easier to start conversations\n2. **Read name tags** - Great conversation starters\n3. **Ask open questions** - \"What brings you here?\"\n4. **Listen actively** - People love good listeners\n5. **Follow up later** - Connect within 24-48 hours\n\n💼 **Perfect for:** Professional development, career growth, finding collaborators, and making friends!\n\nWhat type of networking are you interested in?"
    
    elif any(word in message_lower for word in ['help', 'how', 'guide', 'confused']):
        return "💡 **I'm here to help!** Here's what I can assist with:\n\n🎯 **Event Creation:**\n• Choosing venues and timing\n• Writing descriptions\n• Setting capacity\n\n🎟️ **Event Attendance:**\n• Finding the right events\n• Registration tips\n• Networking advice\n\n🔧 **Platform Features:**\n• Navigation help\n• Account management\n• Troubleshooting\n\nJust ask me anything specific! What would you like to know?"
    
    elif any(word in message_lower for word in ['theme', 'dark mode', 'light mode', 'appearance']):
        return "🎨 **Customizing Your Experience:**\n\n🌙 **Dark Mode** - Easy on the eyes, perfect for evening planning\n☀️ **Light Mode** - Bright and clear, great for daytime use\n\n💡 **Toggle anytime** using the moon/sun icon in the navigation! Your preference is saved automatically.\n\n✨ Both themes are designed to make event planning beautiful and enjoyable!"
    
    elif any(word in message_lower for word in ['thank', 'thanks', 'awesome', 'great', 'good']):
        return "🌟 **You're so welcome!** I'm thrilled to help make your event experience amazing!\n\n🎉 **Remember:** Great events start with great planning. Whether you're creating your first event or attending your 50th, I'm here to help every step of the way.\n\n💫 **Keep exploring** and don't hesitate to ask if you need anything else. Happy event planning! 🚀"
    
    else:
        # More helpful default response with context
        return f"🤖 **Great question!** I'm your Event Planning Assistant, and I'd love to help you with:\n\n🎯 **Event Creation**: venue selection, timing, capacity, descriptions\n🎟️ **Event Attendance**: finding events, registration tips, networking\n⚙️ **Platform Help**: navigation, features, troubleshooting\n\n💬 **Try asking me about:**\n• \"How do I create an engaging event?\"\n• \"What's the best venue for my event?\"\n• \"How do I network effectively?\"\n• \"When should I schedule my event?\"\n\nWhat would you like help with today?"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
