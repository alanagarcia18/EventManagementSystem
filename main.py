import tkinter as tk
from tkinter import ttk, messagebox, font
from db import DB
from datetime import datetime, timedelta
import re

class EventApp(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("Event Management System")
		self.geometry("1200x800")
		self.minsize(1000, 600)
		
		# Configure colors and styling
		self.configure(bg='#f0f0f0')
		
		self.db = DB()
		self.current_user = None

		self.setup_styles()
		self.create_widgets()

	def setup_styles(self):
		"""Configure custom styles for the application"""
		style = ttk.Style()
		style.theme_use('clam')
		
		# Configure styles
		style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
		style.configure('Heading.TLabel', font=('Arial', 12, 'bold'), foreground='#34495e')
		style.configure('Info.TLabel', font=('Arial', 10), foreground='#7f8c8d')
		style.configure('Success.TLabel', font=('Arial', 10), foreground='#27ae60')
		style.configure('Error.TLabel', font=('Arial', 10), foreground='#e74c3c')
		
		# Button styles
		style.configure('Primary.TButton', padding=(10, 5))
		style.configure('Secondary.TButton', padding=(8, 4))
		style.configure('Danger.TButton', foreground='white', background='#e74c3c')
		
		# Frame styles
		style.configure('Card.TFrame', relief='solid', borderwidth=1, background='white')
		style.configure('Sidebar.TFrame', background='#34495e')

	def create_widgets(self):
		# Create main container
		main_container = ttk.Frame(self)
		main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
		
		# Header frame with improved styling
		self.create_header(main_container)
		
		# Main content area with sidebar
		content_frame = ttk.Frame(main_container)
		content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
		
		# Configure grid weights
		content_frame.grid_rowconfigure(0, weight=1)
		content_frame.grid_columnconfigure(1, weight=1)
		
		# Create sidebar navigation
		self.create_sidebar(content_frame)
		
		# Create main content area
		self.create_content_area(content_frame)

	def create_header(self, parent):
		"""Create an improved header with user info and login"""
		header_frame = ttk.Frame(parent, style='Card.TFrame')
		header_frame.pack(fill=tk.X, pady=(0, 10))
		
		# App title
		title_frame = ttk.Frame(header_frame)
		title_frame.pack(fill=tk.X, padx=15, pady=10)
		
		ttk.Label(title_frame, text="🎯 Event Management System", 
				 style='Title.TLabel').pack(side=tk.LEFT)
		
		# User info and controls
		user_frame = ttk.Frame(title_frame)
		user_frame.pack(side=tk.RIGHT)
		
		# Current user display
		self.user_info_frame = ttk.Frame(user_frame)
		self.user_info_frame.pack(side=tk.RIGHT, padx=(0, 10))
		
		self.role_label = ttk.Label(self.user_info_frame, text="Not logged in", 
								   style='Info.TLabel')
		self.role_label.pack()
		
		# Login controls
		login_frame = ttk.Frame(user_frame)
		login_frame.pack(side=tk.RIGHT)
		
		ttk.Label(login_frame, text="User:", style='Heading.TLabel').pack(side=tk.LEFT)
		
		self.user_var = tk.StringVar()
		self.user_combo = ttk.Combobox(login_frame, textvariable=self.user_var, 
									  width=25, state="readonly")
		self.refresh_user_list()
		self.user_combo.pack(side=tk.LEFT, padx=(5, 10))
		
		ttk.Button(login_frame, text="New User", command=self.create_user_dialog,
				  style='Secondary.TButton').pack(side=tk.LEFT, padx=2)
		ttk.Button(login_frame, text="Login", command=self.login,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=2)

	def create_sidebar(self, parent):
		"""Create an improved sidebar navigation"""
		sidebar_frame = ttk.Frame(parent, style='Card.TFrame', width=200)
		sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
		sidebar_frame.grid_propagate(False)
		
		# Sidebar title
		ttk.Label(sidebar_frame, text="Navigation", 
				 style='Heading.TLabel').pack(pady=(15, 10))
		
		# Navigation buttons with icons
		nav_buttons = [
			("🔍 Browse Events", self.show_browse),
			("📋 My Registrations", self.show_my_regs),
			("🎪 Organizer Panel", self.show_organizer),
			("⚙️ Admin Panel", self.show_admin)
		]
		
		for text, command in nav_buttons:
			btn = ttk.Button(sidebar_frame, text=text, command=command)
			btn.pack(fill=tk.X, padx=15, pady=2)

	def create_content_area(self, parent):
		"""Create the main content area"""
		# Right: content with notebook for better organization
		self.content_notebook = ttk.Notebook(parent)
		self.content_notebook.grid(row=0, column=1, sticky="nsew")
		
		# Create frames for different functionalities
		self.frames = {}
		frame_configs = [
			(BrowseFrame, "🔍 Browse Events"),
			(MyRegsFrame, "📋 My Registrations"),
			(OrganizerFrame, "🎪 Organizer Panel"),
			(AdminFrame, "⚙️ Admin Panel")
		]
		
		for frame_class, title in frame_configs:
			frame = frame_class(self.content_notebook, self)
			self.frames[frame_class.__name__] = frame
			self.content_notebook.add(frame, text=title)
		
		# Start with browse events
		self.content_notebook.select(0)

	def refresh_user_list(self):
		users = [f"{u[1]} <{u[2]}> ({u[3]})" for u in self.db.get_users()]
		self.user_combo['values'] = users

	def create_user_dialog(self):
		dlg = tk.Toplevel(self)
		dlg.title("Create New User")
		dlg.geometry("400x300")
		dlg.resizable(False, False)
		dlg.transient(self)
		dlg.grab_set()
		
		# Center the dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (400 // 2)
		y = (dlg.winfo_screenheight() // 2) - (300 // 2)
		dlg.geometry(f"400x300+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Title
		ttk.Label(main_frame, text="Create New User Account", 
				 style='Title.TLabel').pack(pady=(0, 20))
		
		# Form fields
		form_frame = ttk.Frame(main_frame)
		form_frame.pack(fill=tk.X, pady=10)
		
		fields = [
			("Full Name:", "name"),
			("Email Address:", "email"),
			("Role:", "role")
		]
		
		entries = {}
		for i, (label_text, field_name) in enumerate(fields):
			ttk.Label(form_frame, text=label_text, style='Heading.TLabel').grid(
				row=i, column=0, sticky="w", padx=(0, 10), pady=5)
			
			if field_name == "role":
				entry = ttk.Combobox(form_frame, values=["attendee", "organizer", "admin"], 
								   state="readonly", width=25)
				entry.set("attendee")  # Default value
			else:
				entry = ttk.Entry(form_frame, width=25, font=('Arial', 10))
			
			entry.grid(row=i, column=1, sticky="ew", pady=5)
			entries[field_name] = entry
		
		form_frame.grid_columnconfigure(1, weight=1)

		def create_user():
			name = entries["name"].get().strip()
			email = entries["email"].get().strip()
			role = entries["role"].get().strip() or 'attendee'
			
			# Validation
			if not name or not email:
				messagebox.showerror("Error", "Name and email are required!")
				return
			
			# Email validation
			email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
			if not re.match(email_pattern, email):
				messagebox.showerror("Error", "Please enter a valid email address!")
				return
			
			try:
				self.db.create_user(name, email, role)
				messagebox.showinfo("Success", f"User '{name}' created successfully!")
				self.refresh_user_list()
				dlg.destroy()
			except Exception as ex:
				messagebox.showerror("Error", str(ex))

		# Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill=tk.X, pady=(20, 0))
		
		ttk.Button(button_frame, text="Cancel", command=dlg.destroy,
				  style='Secondary.TButton').pack(side=tk.RIGHT, padx=5)
		ttk.Button(button_frame, text="Create User", command=create_user,
				  style='Primary.TButton').pack(side=tk.RIGHT)

	def login(self):
		sel = self.user_var.get()
		if not sel:
			messagebox.showwarning("Login Required", "Please select a user or create a new account")
			return
		
		# extract email from "Name <email> (role)"
		try:
			email = sel.split('<')[1].split('>')[0]
		except Exception:
			messagebox.showerror("Login Error", "Could not parse selected user")
			return
		
		user = self.db.get_user_by_email(email)
		if not user:
			messagebox.showerror("Login Error", "User not found")
			return
		
		self.current_user = user
		self.role_label.config(text=f"✅ {user[1]} ({user[3]})", style='Success.TLabel')
		
		# Show welcome message
		messagebox.showinfo("Welcome!", f"Welcome back, {user[1]}!\nRole: {user[3].title()}")
		
		# refresh panels
		for f in self.frames.values():
			if hasattr(f, 'refresh'):
				f.refresh()

	def show_frame(self, frame_name):
		"""Switch to a specific frame by selecting the corresponding tab"""
		frame_mapping = {
			'BrowseFrame': 0,
			'MyRegsFrame': 1, 
			'OrganizerFrame': 2,
			'AdminFrame': 3
		}
		
		tab_index = frame_mapping.get(frame_name)
		if tab_index is not None:
			self.content_notebook.select(tab_index)

	def show_browse(self):
		self.show_frame('BrowseFrame')

	def show_my_regs(self):
		self.show_frame('MyRegsFrame')

	def show_organizer(self):
		if not self.current_user or self.current_user[3] not in ['organizer', 'admin']:
			messagebox.showwarning("Access Denied", 
								 "Organizer panel requires an organizer or admin account.\nPlease login with appropriate permissions.")
			return
		self.show_frame('OrganizerFrame')

	def show_admin(self):
		if not self.current_user or self.current_user[3] != 'admin':
			messagebox.showwarning("Access Denied", 
								 "Admin panel requires an administrator account.\nPlease login as an admin.")
			return
		self.show_frame('AdminFrame')


class BrowseFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.search_var = tk.StringVar()
		self.search_var.trace('w', self.on_search_change)
		
		self.create_widgets()
		self.populate()

	def create_widgets(self):
		# Header with search
		header_frame = ttk.Frame(self, style='Card.TFrame')
		header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
		
		header_content = ttk.Frame(header_frame)
		header_content.pack(fill=tk.X, padx=15, pady=10)
		
		ttk.Label(header_content, text="🔍 Browse Events", 
				 style='Title.TLabel').pack(side=tk.LEFT)
		
		# Search frame
		search_frame = ttk.Frame(header_content)
		search_frame.pack(side=tk.RIGHT)
		
		ttk.Label(search_frame, text="Search:", style='Heading.TLabel').pack(side=tk.LEFT)
		search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
		search_entry.pack(side=tk.LEFT, padx=(5, 10))
		
		ttk.Button(search_frame, text="🔄 Refresh", command=self.populate,
				  style='Secondary.TButton').pack(side=tk.LEFT)

		# Events list with improved styling
		list_frame = ttk.Frame(self, style='Card.TFrame')
		list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
		
		# Configure treeview with better columns
		columns = ("title", "venue", "start", "capacity", "registered")
		self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
		
		# Configure column headings and widths
		column_configs = {
			"title": ("Event Title", 250),
			"venue": ("Venue", 150),
			"start": ("Date & Time", 150),
			"capacity": ("Capacity", 80),
			"registered": ("Registered", 80)
		}
		
		for col, (heading, width) in column_configs.items():
			self.tree.heading(col, text=heading)
			self.tree.column(col, width=width, anchor='center' if col in ['capacity', 'registered'] else 'w')
		
		# Scrollbars
		v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscrollcommand=v_scrollbar.set)
		
		# Pack treeview and scrollbars
		self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
		v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)

		# Action buttons
		button_frame = ttk.Frame(self)
		button_frame.pack(fill=tk.X, padx=25, pady=10)
		
		ttk.Button(button_frame, text="📋 View Details", command=self.show_details,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
		ttk.Button(button_frame, text="✅ Register for Event", command=self.register,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
		
		# Status info
		self.status_label = ttk.Label(button_frame, text="", style='Info.TLabel')
		self.status_label.pack(side=tk.RIGHT)

	def on_search_change(self, *args):
		"""Handle real-time search"""
		# Add a small delay to avoid too frequent updates
		if hasattr(self, '_search_timer'):
			self.after_cancel(self._search_timer)
		self._search_timer = self.after(300, self.populate)

	def populate(self):
		# Clear existing items
		for item in self.tree.get_children():
			self.tree.delete(item)
		
		query = self.search_var.get().strip()
		events = self.app.db.search_events(query) if query else self.app.db.get_events()
		
		for event in events:
			# Get registration count
			registered_count = len(self.app.db.get_event_attendees(event['id']))
			
			# Format the start time
			start_time = event.get('start', 'TBD')
			if start_time and start_time != 'TBD':
				try:
					# Format datetime for display
					dt = datetime.fromisoformat(start_time.replace('T', ' '))
					start_time = dt.strftime("%Y-%m-%d %H:%M")
				except:
					pass  # Keep original format if parsing fails
			
			venue_name = event.get('venue_name', 'TBD')
			capacity = event.get('capacity', 0)
			
			# Color coding based on availability
			tags = []
			if registered_count >= capacity:
				tags.append('full')
			elif registered_count >= capacity * 0.8:
				tags.append('almost_full')
			
			self.tree.insert('', tk.END, 
							iid=event['id'], 
							values=(event['title'], venue_name, start_time, 
									capacity, registered_count),
							tags=tags)
		
		# Configure tag colors
		self.tree.tag_configure('full', background='#ffebee', foreground='#c62828')
		self.tree.tag_configure('almost_full', background='#fff3e0', foreground='#f57c00')
		
		# Update status
		event_count = len(events)
		self.status_label.config(text=f"Showing {event_count} event{'s' if event_count != 1 else ''}")

	def show_details(self):
		selection = self.tree.focus()
		if not selection:
			messagebox.showinfo("No Selection", "Please select an event to view details")
			return
		
		event_id = int(selection)
		event = self.app.db.get_event(event_id)
		attendees = self.app.db.get_event_attendees(event_id)
		
		if not event:
			messagebox.showerror("Error", "Event not found")
			return
		
		# Create a detailed dialog
		self.show_event_details_dialog(event, attendees)

	def show_event_details_dialog(self, event, attendees):
		"""Show a detailed event information dialog"""
		dlg = tk.Toplevel(self.app)
		dlg.title("Event Details")
		dlg.geometry("600x500")
		dlg.resizable(False, False)
		dlg.transient(self.app)
		dlg.grab_set()
		
		# Center dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (600 // 2)
		y = (dlg.winfo_screenheight() // 2) - (500 // 2)
		dlg.geometry(f"600x500+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Event title
		ttk.Label(main_frame, text=event['title'], 
				 style='Title.TLabel').pack(pady=(0, 15))
		
		# Event details in a scrollable text widget
		details_frame = ttk.LabelFrame(main_frame, text="Event Information", padding=15)
		details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
		
		details_text = tk.Text(details_frame, wrap=tk.WORD, height=15, width=60,
							  font=('Arial', 10), background='white')
		details_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, 
									  command=details_text.yview)
		details_text.configure(yscrollcommand=details_scroll.set)
		
		# Format event information
		info_text = f"""📝 Description:
{event.get('description', 'No description available')}

🏢 Venue: {event.get('venue_name', 'TBD')}

📅 Date & Time: {event.get('start', 'TBD')}

👥 Capacity: {event.get('capacity', 'Unlimited')} people
👤 Currently Registered: {len(attendees)} people

📋 Attendee List:"""

		if attendees:
			for i, attendee in enumerate(attendees, 1):
				info_text += f"\n{i}. {attendee['name']} ({attendee['email']})"
		else:
			info_text += "\nNo registrations yet."
		
		details_text.insert(tk.END, info_text)
		details_text.config(state=tk.DISABLED)  # Make read-only
		
		details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
		
		# Action buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill=tk.X, pady=(15, 0))
		
		ttk.Button(button_frame, text="Close", command=dlg.destroy,
				  style='Secondary.TButton').pack(side=tk.RIGHT, padx=5)

	def register(self):
		if not self.app.current_user:
			messagebox.showwarning("Login Required", 
								 "Please login to register for events")
			return
		
		selection = self.tree.focus()
		if not selection:
			messagebox.showwarning("No Selection", 
								 "Please select an event to register for")
			return
		
		event_id = int(selection)
		event = self.app.db.get_event(event_id)
		
		# Confirm registration
		result = messagebox.askyesno("Confirm Registration", 
									f"Register for '{event['title']}'?\n\n"
									f"Venue: {event.get('venue_name', 'TBD')}\n"
									f"Date: {event.get('start', 'TBD')}")
		
		if not result:
			return
		
		try:
			self.app.db.register_user_for_event(self.app.current_user[0], event_id)
			messagebox.showinfo("Registration Successful", 
							   f"You are now registered for '{event['title']}'!")
			self.populate()  # Refresh the list
			
			# Refresh My Registrations tab if it exists
			if hasattr(self.app.frames['MyRegsFrame'], 'refresh'):
				self.app.frames['MyRegsFrame'].refresh()
				
		except Exception as ex:
			messagebox.showerror("Registration Failed", str(ex))


class MyRegsFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.create_widgets()
		self.refresh()

	def create_widgets(self):
		# Header
		header_frame = ttk.Frame(self, style='Card.TFrame')
		header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
		
		header_content = ttk.Frame(header_frame)
		header_content.pack(fill=tk.X, padx=15, pady=10)
		
		ttk.Label(header_content, text="📋 My Event Registrations", 
				 style='Title.TLabel').pack(side=tk.LEFT)
		
		ttk.Button(header_content, text="🔄 Refresh", command=self.refresh,
				  style='Secondary.TButton').pack(side=tk.RIGHT)

		# Registrations list
		list_frame = ttk.Frame(self, style='Card.TFrame')
		list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
		
		# Configure treeview
		columns = ("title", "venue", "start", "capacity", "status")
		self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
		
		# Configure columns
		column_configs = {
			"title": ("Event Title", 250),
			"venue": ("Venue", 150),
			"start": ("Date & Time", 150),
			"capacity": ("Capacity", 80),
			"status": ("Status", 100)
		}
		
		for col, (heading, width) in column_configs.items():
			self.tree.heading(col, text=heading)
			self.tree.column(col, width=width, anchor='center' if col in ['capacity', 'status'] else 'w')
		
		# Scrollbars
		v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscrollcommand=v_scrollbar.set)
		
		self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
		v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)

		# Action buttons
		button_frame = ttk.Frame(self)
		button_frame.pack(fill=tk.X, padx=25, pady=10)
		
		ttk.Button(button_frame, text="📋 View Details", command=self.show_details,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
		ttk.Button(button_frame, text="❌ Cancel Registration", command=self.cancel_registration,
				  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
		
		# Status info
		self.status_label = ttk.Label(button_frame, text="", style='Info.TLabel')
		self.status_label.pack(side=tk.RIGHT)

	def refresh(self):
		# Clear existing items
		for item in self.tree.get_children():
			self.tree.delete(item)
		
		if not self.app.current_user:
			self.status_label.config(text="Please login to view registrations")
			return
		
		registrations = self.app.db.get_registrations_by_user(self.app.current_user[0])
		
		for reg in registrations:
			# Format start time
			start_time = reg.get('start', 'TBD')
			if start_time and start_time != 'TBD':
				try:
					dt = datetime.fromisoformat(start_time.replace('T', ' '))
					start_time = dt.strftime("%Y-%m-%d %H:%M")
					
					# Determine status based on date
					now = datetime.now()
					if dt < now:
						status = "Past"
						tags = ['past']
					elif dt - now < timedelta(days=1):
						status = "Soon"
						tags = ['soon']
					else:
						status = "Upcoming"
						tags = ['upcoming']
				except:
					status = "Unknown"
					tags = []
			else:
				status = "TBD"
				tags = []
			
			venue_name = reg.get('venue_name', 'TBD')
			capacity = reg.get('capacity', 0)
			
			self.tree.insert('', tk.END, 
							iid=reg['event_id'], 
							values=(reg['title'], venue_name, start_time, capacity, status),
							tags=tags)
		
		# Configure tag colors
		self.tree.tag_configure('past', background='#f5f5f5', foreground='#757575')
		self.tree.tag_configure('soon', background='#fff3e0', foreground='#f57c00')
		self.tree.tag_configure('upcoming', background='#e8f5e8', foreground='#2e7d32')
		
		reg_count = len(registrations)
		self.status_label.config(text=f"{reg_count} registration{'s' if reg_count != 1 else ''}")

	def show_details(self):
		selection = self.tree.focus()
		if not selection:
			messagebox.showinfo("No Selection", "Please select a registration to view details")
			return
		
		event_id = int(selection)
		event = self.app.db.get_event(event_id)
		attendees = self.app.db.get_event_attendees(event_id)
		
		# Reuse the details dialog from BrowseFrame
		browse_frame = self.app.frames.get('BrowseFrame')
		if browse_frame:
			browse_frame.show_event_details_dialog(event, attendees)

	def cancel_registration(self):
		if not self.app.current_user:
			messagebox.showwarning("Login Required", "Please login to cancel registrations")
			return
		
		selection = self.tree.focus()
		if not selection:
			messagebox.showwarning("No Selection", "Please select a registration to cancel")
			return
		
		event_id = int(selection)
		event = self.app.db.get_event(event_id)
		
		# Confirm cancellation
		result = messagebox.askyesno("Confirm Cancellation", 
									f"Cancel registration for '{event['title']}'?\n\n"
									"This action cannot be undone.")
		
		if not result:
			return
		
		try:
			self.app.db.unregister_user_from_event(self.app.current_user[0], event_id)
			messagebox.showinfo("Registration Cancelled", 
							   f"Registration for '{event['title']}' has been cancelled.")
			self.refresh()
			
			# Refresh browse events tab
			if hasattr(self.app.frames['BrowseFrame'], 'populate'):
				self.app.frames['BrowseFrame'].populate()
				
		except Exception as ex:
			messagebox.showerror("Cancellation Failed", str(ex))


class OrganizerFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.create_widgets()
		self.refresh()

	def create_widgets(self):
		# Header
		header_frame = ttk.Frame(self, style='Card.TFrame')
		header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
		
		header_content = ttk.Frame(header_frame)
		header_content.pack(fill=tk.X, padx=15, pady=10)
		
		ttk.Label(header_content, text="🎪 Event Organizer Panel", 
				 style='Title.TLabel').pack(side=tk.LEFT)
		
		button_group = ttk.Frame(header_content)
		button_group.pack(side=tk.RIGHT)
		
		ttk.Button(button_group, text="➕ Create Event", command=self.create_event,
				  style='Primary.TButton').pack(side=tk.RIGHT, padx=5)
		ttk.Button(button_group, text="🔄 Refresh", command=self.refresh,
				  style='Secondary.TButton').pack(side=tk.RIGHT)

		# Events list
		list_frame = ttk.Frame(self, style='Card.TFrame')
		list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
		
		# Configure treeview
		columns = ("title", "venue", "start", "capacity", "registered", "status")
		self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
		
		# Configure columns
		column_configs = {
			"title": ("Event Title", 200),
			"venue": ("Venue", 130),
			"start": ("Date & Time", 130),
			"capacity": ("Capacity", 70),
			"registered": ("Registered", 80),
			"status": ("Status", 80)
		}
		
		for col, (heading, width) in column_configs.items():
			self.tree.heading(col, text=heading)
			self.tree.column(col, width=width, anchor='center' if col in ['capacity', 'registered', 'status'] else 'w')
		
		# Scrollbars
		v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscrollcommand=v_scrollbar.set)
		
		self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
		v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)

		# Action buttons
		button_frame = ttk.Frame(self)
		button_frame.pack(fill=tk.X, padx=25, pady=10)
		
		ttk.Button(button_frame, text="📋 View Details", command=self.view_event_details,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
		ttk.Button(button_frame, text="👥 Manage Attendees", command=self.manage_attendees,
				  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
		
		# Status info
		self.status_label = ttk.Label(button_frame, text="", style='Info.TLabel')
		self.status_label.pack(side=tk.RIGHT)

	def refresh(self):
		# Clear existing items
		for item in self.tree.get_children():
			self.tree.delete(item)
		
		if not self.app.current_user:
			self.status_label.config(text="Please login as organizer")
			return
		
		events = self.app.db.get_events_by_organizer(self.app.current_user[0])
		
		for event in events:
			# Get registration count
			registered_count = len(self.app.db.get_event_attendees(event['id']))
			
			# Format start time and determine status
			start_time = event.get('start', 'TBD')
			status = "Active"
			tags = []
			
			if start_time and start_time != 'TBD':
				try:
					dt = datetime.fromisoformat(start_time.replace('T', ' '))
					start_time = dt.strftime("%Y-%m-%d %H:%M")
					
					now = datetime.now()
					if dt < now:
						status = "Past"
						tags = ['past']
					elif dt - now < timedelta(days=1):
						status = "Soon"
						tags = ['soon']
					else:
						status = "Upcoming"
						tags = ['upcoming']
				except:
					pass
			
			venue_name = event.get('venue_name', 'TBD')
			capacity = event.get('capacity', 0)
			
			# Add color coding for capacity
			if registered_count >= capacity:
				tags.append('full')
			elif registered_count >= capacity * 0.8:
				tags.append('almost_full')
			
			self.tree.insert('', tk.END, 
							iid=event['id'], 
							values=(event['title'], venue_name, start_time, 
									capacity, registered_count, status),
							tags=tags)
		
		# Configure tag colors
		self.tree.tag_configure('past', background='#f5f5f5', foreground='#757575')
		self.tree.tag_configure('soon', background='#fff3e0', foreground='#f57c00')
		self.tree.tag_configure('upcoming', background='#e8f5e8', foreground='#2e7d32')
		self.tree.tag_configure('full', background='#ffebee')
		self.tree.tag_configure('almost_full', background='#fff8e1')
		
		event_count = len(events)
		self.status_label.config(text=f"{event_count} event{'s' if event_count != 1 else ''}")

	def create_event(self):
		dlg = tk.Toplevel(self.app)
		dlg.title('Create New Event')
		dlg.geometry("500x450")
		dlg.resizable(False, False)
		dlg.transient(self.app)
		dlg.grab_set()
		
		# Center dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (500 // 2)
		y = (dlg.winfo_screenheight() // 2) - (450 // 2)
		dlg.geometry(f"500x450+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Title
		ttk.Label(main_frame, text="Create New Event", 
				 style='Title.TLabel').pack(pady=(0, 20))
		
		# Form fields
		fields = {}
		
		# Title
		ttk.Label(main_frame, text="Event Title*:", style='Heading.TLabel').pack(anchor='w', pady=(0,5))
		fields['title'] = ttk.Entry(main_frame, width=50, font=('Arial', 10))
		fields['title'].pack(fill=tk.X, pady=(0,10))
		
		# Description
		ttk.Label(main_frame, text="Description:", style='Heading.TLabel').pack(anchor='w', pady=(0,5))
		fields['description'] = ttk.Entry(main_frame, width=50, font=('Arial', 10))
		fields['description'].pack(fill=tk.X, pady=(0,10))
		
		# Venue
		ttk.Label(main_frame, text="Venue*:", style='Heading.TLabel').pack(anchor='w', pady=(0,5))
		venues = self.app.db.get_venues()
		venue_options = [f"{v[1]} - {v[2]} (Cap: {v[3]})" for v in venues]
		venue_map = {f"{v[1]} - {v[2]} (Cap: {v[3]})": v[0] for v in venues}
		fields['venue'] = ttk.Combobox(main_frame, values=venue_options, state="readonly", width=47)
		fields['venue'].pack(fill=tk.X, pady=(0,10))
		
		# Capacity
		ttk.Label(main_frame, text="Event Capacity*:", style='Heading.TLabel').pack(anchor='w', pady=(0,5))
		fields['capacity'] = ttk.Entry(main_frame, width=50)
		fields['capacity'].pack(fill=tk.X, pady=(0,10))
		
		# Start Date and Time
		ttk.Label(main_frame, text="Start Date (YYYY-MM-DD)*:", style='Heading.TLabel').pack(anchor='w', pady=(0,5))
		fields['start_date'] = ttk.Entry(main_frame, width=50)
		fields['start_date'].pack(fill=tk.X, pady=(0,5))
		fields['start_date'].insert(0, datetime.now().strftime("%Y-%m-%d"))
		
		ttk.Label(main_frame, text="Start Time (HH:MM)*:", style='Heading.TLabel').pack(anchor='w', pady=(0,5))
		fields['start_time'] = ttk.Entry(main_frame, width=50)
		fields['start_time'].pack(fill=tk.X, pady=(0,15))
		fields['start_time'].insert(0, "09:00")

		def create_event_action():
			title = fields['title'].get().strip()
			description = fields['description'].get().strip()
			venue_selection = fields['venue'].get()
			venue_id = venue_map.get(venue_selection)
			
			try:
				capacity = int(fields['capacity'].get().strip())
			except ValueError:
				messagebox.showerror('Error', 'Please enter a valid capacity number')
				return
			
			start_date = fields['start_date'].get().strip()
			start_time = fields['start_time'].get().strip()
			
			# Validation
			if not all([title, venue_id, start_date, start_time]):
				messagebox.showerror('Error', 'Please fill in all required fields (marked with *)')
				return
			
			# Validate date format
			try:
				start_datetime = f"{start_date} {start_time}"
				datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
			except ValueError:
				messagebox.showerror('Error', 'Please enter valid date and time formats')
				return
			
			try:
				self.app.db.create_event(title, description, venue_id, 
										self.app.current_user[0], capacity, 
										start_datetime)
				messagebox.showinfo('Success', 'Event created successfully!')
				dlg.destroy()
				self.refresh()
			except Exception as ex:
				messagebox.showerror('Error', str(ex))

		# Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill=tk.X, pady=(20, 0))
		
		ttk.Button(button_frame, text="Cancel", command=dlg.destroy,
				  style='Secondary.TButton').pack(side=tk.RIGHT, padx=5)
		ttk.Button(button_frame, text="Create Event", command=create_event_action,
				  style='Primary.TButton').pack(side=tk.RIGHT)

	def view_event_details(self):
		selection = self.tree.focus()
		if not selection:
			messagebox.showinfo("No Selection", "Please select an event to view details")
			return
		
		event_id = int(selection)
		event = self.app.db.get_event(event_id)
		attendees = self.app.db.get_event_attendees(event_id)
		
		# Reuse the details dialog from BrowseFrame
		browse_frame = self.app.frames.get('BrowseFrame')
		if browse_frame:
			browse_frame.show_event_details_dialog(event, attendees)

	def manage_attendees(self):
		selection = self.tree.focus()
		if not selection:
			messagebox.showinfo("No Selection", "Please select an event to manage attendees")
			return
		
		event_id = int(selection)
		event = self.app.db.get_event(event_id)
		attendees = self.app.db.get_event_attendees(event_id)
		
		# Create attendee management dialog
		dlg = tk.Toplevel(self.app)
		dlg.title(f"Manage Attendees - {event['title']}")
		dlg.geometry("700x500")
		dlg.transient(self.app)
		dlg.grab_set()
		
		# Center dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (700 // 2)
		y = (dlg.winfo_screenheight() // 2) - (500 // 2)
		dlg.geometry(f"700x500+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Title
		ttk.Label(main_frame, text=f"Attendees for: {event['title']}", 
				 style='Title.TLabel').pack(pady=(0, 15))
		
		# Attendees list
		list_frame = ttk.LabelFrame(main_frame, text=f"Registered Attendees ({len(attendees)}/{event['capacity']})", 
								   padding=10)
		list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
		
		columns = ("name", "email", "registration_date")
		attendee_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
		
		attendee_tree.heading("name", text="Name")
		attendee_tree.heading("email", text="Email")
		attendee_tree.heading("registration_date", text="Registration Date")
		
		attendee_tree.column("name", width=200)
		attendee_tree.column("email", width=250)
		attendee_tree.column("registration_date", width=150)
		
		for attendee in attendees:
			reg_date = attendee.get('registration_date', '')
			if reg_date:
				try:
					dt = datetime.fromisoformat(reg_date.replace('T', ' '))
					reg_date = dt.strftime("%Y-%m-%d %H:%M")
				except:
					pass
			
			attendee_tree.insert('', tk.END, values=(
				attendee['name'], attendee['email'], reg_date
			))
		
		attendee_tree.pack(fill=tk.BOTH, expand=True)
		
		# Close button
		ttk.Button(main_frame, text="Close", command=dlg.destroy,
				  style='Primary.TButton').pack(pady=(15, 0))


class AdminFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.create_widgets()

	def create_widgets(self):
		# Header
		header_frame = ttk.Frame(self, style='Card.TFrame')
		header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
		
		header_content = ttk.Frame(header_frame)
		header_content.pack(fill=tk.X, padx=15, pady=10)
		
		ttk.Label(header_content, text="⚙️ Admin Panel", 
				 style='Title.TLabel').pack(side=tk.LEFT)
		
		ttk.Button(header_content, text="📊 View Statistics", command=self.show_statistics,
				  style='Primary.TButton').pack(side=tk.RIGHT)

		# Management options
		management_frame = ttk.Frame(self, style='Card.TFrame')
		management_frame.pack(fill=tk.X, padx=10, pady=5)
		
		content_frame = ttk.Frame(management_frame)
		content_frame.pack(fill=tk.X, padx=15, pady=15)
		
		ttk.Label(content_frame, text="System Management", 
				 style='Heading.TLabel').pack(anchor='w', pady=(0, 10))
		
		# Management buttons
		button_frame = ttk.Frame(content_frame)
		button_frame.pack(fill=tk.X)
		
		ttk.Button(button_frame, text="🏢 Manage Venues", command=self.manage_venues,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
		ttk.Button(button_frame, text="👥 Manage Users", command=self.manage_users,
				  style='Primary.TButton').pack(side=tk.LEFT, padx=5)

	def show_statistics(self):
		"""Show system statistics"""
		stats = self.app.db.get_event_statistics()
		
		dlg = tk.Toplevel(self.app)
		dlg.title("System Statistics")
		dlg.geometry("400x300")
		dlg.resizable(False, False)
		dlg.transient(self.app)
		dlg.grab_set()
		
		# Center dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (400 // 2)
		y = (dlg.winfo_screenheight() // 2) - (300 // 2)
		dlg.geometry(f"400x300+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		ttk.Label(main_frame, text="📊 System Statistics", 
				 style='Title.TLabel').pack(pady=(0, 20))
		
		stats_frame = ttk.Frame(main_frame)
		stats_frame.pack(fill=tk.X)
		
		stat_items = [
			("🎭 Total Events", stats['total_events']),
			("👥 Total Users", stats['total_users']),
			("🏢 Total Venues", stats['total_venues']),
			("📝 Total Registrations", stats['total_registrations'])
		]
		
		for text, value in stat_items:
			row_frame = ttk.Frame(stats_frame)
			row_frame.pack(fill=tk.X, pady=5)
			
			ttk.Label(row_frame, text=text, style='Heading.TLabel').pack(side=tk.LEFT)
			ttk.Label(row_frame, text=str(value), style='Info.TLabel').pack(side=tk.RIGHT)
		
		ttk.Button(main_frame, text="Close", command=dlg.destroy,
				  style='Primary.TButton').pack(pady=(20, 0))

	def manage_venues(self):
		dlg = tk.Toplevel(self.app)
		dlg.title('Venue Management')
		dlg.geometry("800x600")
		dlg.transient(self.app)
		dlg.grab_set()
		
		# Center dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (800 // 2)
		y = (dlg.winfo_screenheight() // 2) - (600 // 2)
		dlg.geometry(f"800x600+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Header
		header_frame = ttk.Frame(main_frame)
		header_frame.pack(fill=tk.X, pady=(0, 15))
		
		ttk.Label(header_frame, text="🏢 Venue Management", 
				 style='Title.TLabel').pack(side=tk.LEFT)
		ttk.Button(header_frame, text="➕ Add New Venue", command=lambda: self.add_venue(dlg),
				  style='Primary.TButton').pack(side=tk.RIGHT)
		
		# Venues list
		columns = ("name", "address", "capacity")
		tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
		
		tree.heading('name', text='Venue Name')
		tree.heading('address', text='Address')
		tree.heading('capacity', text='Capacity')
		
		tree.column('name', width=200)
		tree.column('address', width=300)
		tree.column('capacity', width=100, anchor='center')
		
		# Load venues
		for venue in self.app.db.get_venues():
			tree.insert('', tk.END, iid=venue[0], values=(venue[1], venue[2], venue[3]))
		
		tree.pack(fill=tk.BOTH, expand=True)
		
		# Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill=tk.X, pady=(15, 0))
		
		ttk.Button(button_frame, text="Close", command=dlg.destroy,
				  style='Secondary.TButton').pack(side=tk.RIGHT)

	def add_venue(self, parent_dlg):
		dlg = tk.Toplevel(parent_dlg)
		dlg.title('Add New Venue')
		dlg.geometry("400x300")
		dlg.resizable(False, False)
		dlg.transient(parent_dlg)
		dlg.grab_set()
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		ttk.Label(main_frame, text="Add New Venue", 
				 style='Title.TLabel').pack(pady=(0, 20))
		
		# Form fields
		fields = {}
		field_configs = [
			("Venue Name*:", "name"),
			("Address*:", "address"),
			("Capacity*:", "capacity")
		]
		
		for label_text, field_name in field_configs:
			ttk.Label(main_frame, text=label_text, style='Heading.TLabel').pack(anchor='w', pady=(0,5))
			field = ttk.Entry(main_frame, width=40, font=('Arial', 10))
			field.pack(fill=tk.X, pady=(0,10))
			fields[field_name] = field

		def create_venue():
			name = fields["name"].get().strip()
			address = fields["address"].get().strip()
			
			try:
				capacity = int(fields["capacity"].get().strip())
			except ValueError:
				messagebox.showerror("Error", "Please enter a valid capacity number!")
				return
			
			if not all([name, address]):
				messagebox.showerror("Error", "Name and address are required!")
				return
			
			try:
				self.app.db.create_venue(name, address, capacity)
				messagebox.showinfo("Success", f"Venue '{name}' created successfully!")
				dlg.destroy()
				parent_dlg.destroy()
				self.manage_venues()  # Refresh the venues list
			except Exception as ex:
				messagebox.showerror("Error", str(ex))

		# Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill=tk.X, pady=(20, 0))
		
		ttk.Button(button_frame, text="Cancel", command=dlg.destroy,
				  style='Secondary.TButton').pack(side=tk.RIGHT, padx=5)
		ttk.Button(button_frame, text="Create Venue", command=create_venue,
				  style='Primary.TButton').pack(side=tk.RIGHT)

	def manage_users(self):
		dlg = tk.Toplevel(self.app)
		dlg.title('User Management')
		dlg.geometry("600x400")
		dlg.transient(self.app)
		dlg.grab_set()
		
		# Center dialog
		dlg.update_idletasks()
		x = (dlg.winfo_screenwidth() // 2) - (600 // 2)
		y = (dlg.winfo_screenheight() // 2) - (400 // 2)
		dlg.geometry(f"600x400+{x}+{y}")
		
		main_frame = ttk.Frame(dlg, style='Card.TFrame')
		main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
		
		# Header
		ttk.Label(main_frame, text="👥 User Management", 
				 style='Title.TLabel').pack(pady=(0, 15))
		
		# Users list
		columns = ("name", "email", "role")
		tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
		
		tree.heading('name', text='Name')
		tree.heading('email', text='Email')
		tree.heading('role', text='Role')
		
		tree.column('name', width=150)
		tree.column('email', width=200)
		tree.column('role', width=100, anchor='center')
		
		# Load users
		for user in self.app.db.get_users():
			tree.insert('', tk.END, iid=user[0], values=(user[1], user[2], user[3]))
		
		tree.pack(fill=tk.BOTH, expand=True)

		def delete_selected_user():
			selection = tree.focus()
			if not selection:
				messagebox.showwarning("No Selection", "Please select a user to delete")
				return
			
			user_id = int(selection)
			user = None
			for u in self.app.db.get_users():
				if u[0] == user_id:
					user = u
					break
			
			if not user:
				messagebox.showerror("Error", "User not found")
				return
			
			# Prevent deleting current user
			if self.app.current_user and user_id == self.app.current_user[0]:
				messagebox.showerror("Error", "Cannot delete the currently logged-in user")
				return
			
			result = messagebox.askyesno("Confirm Deletion", 
										f"Delete user '{user[1]}' ({user[2]})?\n\n"
										"This will also remove all their event registrations.\n"
										"This action cannot be undone.")
			
			if result:
				try:
					self.app.db.delete_user(user_id)
					messagebox.showinfo("Success", f"User '{user[1]}' deleted successfully")
					dlg.destroy()
					self.manage_users()  # Refresh the list
					self.app.refresh_user_list()  # Refresh the main user list
				except Exception as ex:
					messagebox.showerror("Error", str(ex))
		
		# Buttons
		button_frame = ttk.Frame(main_frame)
		button_frame.pack(fill=tk.X, pady=(15, 0))
		
		ttk.Button(button_frame, text="❌ Delete Selected", command=delete_selected_user,
				  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
		ttk.Button(button_frame, text="Close", command=dlg.destroy,
				  style='Secondary.TButton').pack(side=tk.RIGHT)


if __name__ == '__main__':
	app = EventApp()
	app.mainloop()
