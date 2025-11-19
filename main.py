import tkinter as tk
from tkinter import ttk, messagebox
from db import DB


class EventApp(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("Event Management System")
		self.geometry("900x600")

		self.db = DB()
		self.current_user = None

		self.create_widgets()

	def create_widgets(self):
		# Top frame: login / user selector
		top = ttk.Frame(self)
		top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

		ttk.Label(top, text="User:").pack(side=tk.LEFT)
		self.user_var = tk.StringVar()
		self.user_combo = ttk.Combobox(top, textvariable=self.user_var, width=30)
		self.refresh_user_list()
		self.user_combo.pack(side=tk.LEFT, padx=6)

		ttk.Button(top, text="New User", command=self.create_user_dialog).pack(side=tk.LEFT)
		ttk.Button(top, text="Login", command=self.login).pack(side=tk.LEFT, padx=6)

		self.role_label = ttk.Label(top, text="Not logged in")
		self.role_label.pack(side=tk.RIGHT)

		# Main panes
		main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
		main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

		# Left: navigation
		nav = ttk.Frame(main, width=220)
		main.add(nav, weight=1)

		ttk.Button(nav, text="Browse Events", command=self.show_browse).pack(fill=tk.X, pady=4)
		ttk.Button(nav, text="My Registrations", command=self.show_my_regs).pack(fill=tk.X, pady=4)
		ttk.Button(nav, text="Organizer Panel", command=self.show_organizer).pack(fill=tk.X, pady=4)
		ttk.Button(nav, text="Admin Panel", command=self.show_admin).pack(fill=tk.X, pady=4)

		# Right: content
		self.content = ttk.Frame(main)
		main.add(self.content, weight=4)

		self.frames = {}
		for F in (BrowseFrame, MyRegsFrame, OrganizerFrame, AdminFrame):
			frame = F(self.content, self)
			self.frames[F.__name__] = frame
			frame.grid(row=0, column=0, sticky="nsew")

		self.show_browse()

	def refresh_user_list(self):
		users = [f"{u[1]} <{u[2]}> ({u[3]})" for u in self.db.get_users()]
		self.user_combo['values'] = users

	def create_user_dialog(self):
		dlg = tk.Toplevel(self)
		dlg.title("Create User")
		ttk.Label(dlg, text="Name").grid(row=0, column=0)
		name = ttk.Entry(dlg)
		name.grid(row=0, column=1)
		ttk.Label(dlg, text="Email").grid(row=1, column=0)
		email = ttk.Entry(dlg)
		email.grid(row=1, column=1)
		ttk.Label(dlg, text="Role").grid(row=2, column=0)
		role = ttk.Combobox(dlg, values=["attendee", "organizer", "admin"])
		role.grid(row=2, column=1)

		def create():
			n = name.get().strip()
			e = email.get().strip()
			r = role.get().strip() or 'attendee'
			if not n or not e:
				messagebox.showerror("Error", "Name and email required")
				return
			try:
				self.db.create_user(n, e, r)
				messagebox.showinfo("OK", "User created")
				self.refresh_user_list()
				dlg.destroy()
			except Exception as ex:
				messagebox.showerror("Error", str(ex))

		ttk.Button(dlg, text="Create", command=create).grid(row=3, column=0, columnspan=2)

	def login(self):
		sel = self.user_var.get()
		if not sel:
			messagebox.showwarning("Login", "Select a user or create one")
			return
		# extract email from "Name <email> (role)"
		try:
			email = sel.split('<')[1].split('>')[0]
		except Exception:
			messagebox.showerror("Login", "Could not parse selected user")
			return
		user = self.db.get_user_by_email(email)
		if not user:
			messagebox.showerror("Login", "User not found")
			return
		self.current_user = user
		self.role_label.config(text=f"Logged in: {user[1]} ({user[3]})")
		# refresh panels
		for f in self.frames.values():
			if hasattr(f, 'refresh'):
				f.refresh()

	def show_frame(self, name):
		frame = self.frames.get(name)
		if frame:
			frame.tkraise()

	def show_browse(self):
		self.show_frame('BrowseFrame')

	def show_my_regs(self):
		self.show_frame('MyRegsFrame')

	def show_organizer(self):
		if not self.current_user or self.current_user[3] != 'organizer':
			messagebox.showwarning("Access", "Organizer panel requires an organizer login")
			return
		self.show_frame('OrganizerFrame')

	def show_admin(self):
		if not self.current_user or self.current_user[3] != 'admin':
			messagebox.showwarning("Access", "Admin panel requires admin login")
			return
		self.show_frame('AdminFrame')


class BrowseFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.search_var = tk.StringVar()

		top = ttk.Frame(self)
		top.pack(fill=tk.X)
		ttk.Entry(top, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, pady=6)
		ttk.Button(top, text="Search", command=self.populate).pack(side=tk.LEFT, padx=6)

		self.tree = ttk.Treeview(self, columns=("venue","start","capacity"), show='headings')
		self.tree.heading('venue', text='Venue')
		self.tree.heading('start', text='Start')
		self.tree.heading('capacity', text='Capacity')
		self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

		btns = ttk.Frame(self)
		btns.pack(fill=tk.X)
		ttk.Button(btns, text="Details", command=self.show_details).pack(side=tk.LEFT, padx=6)
		ttk.Button(btns, text="Register", command=self.register).pack(side=tk.LEFT)

		self.populate()

	def populate(self):
		for r in self.tree.get_children():
			self.tree.delete(r)
		q = self.search_var.get().strip()
		events = self.app.db.search_events(q) if q else self.app.db.get_events()
		for e in events:
			start = e.get('start') or ''
			venue = e.get('venue_name') or ''
			self.tree.insert('', tk.END, iid=e['id'], values=(venue, start, e['capacity']))

	def show_details(self):
		sel = self.tree.focus()
		if not sel:
			messagebox.showinfo("Details", "Select an event")
			return
		event = self.app.db.get_event(int(sel))
		attendees = self.app.db.get_event_attendees(int(sel))
		txt = f"{event['title']}\n\n{event['description']}\n\nVenue: {event.get('venue_name')}\nStart: {event.get('start')}\nCapacity: {event.get('capacity')}\n\nAttendees: {len(attendees)}"
		messagebox.showinfo("Event Details", txt)

	def register(self):
		if not self.app.current_user:
			messagebox.showwarning("Register", "Login to register")
			return
		sel = self.tree.focus()
		if not sel:
			messagebox.showwarning("Register", "Select an event")
			return
		try:
			self.app.db.register_user_for_event(self.app.current_user[0], int(sel))
			messagebox.showinfo("Registered", "You are registered for the event")
		except Exception as ex:
			messagebox.showerror("Error", str(ex))
		finally:
			if hasattr(self.app.frames['MyRegsFrame'], 'refresh'):
				self.app.frames['MyRegsFrame'].refresh()


class MyRegsFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.tree = ttk.Treeview(self, columns=('start', 'venue'), show='headings')
		self.tree.heading('start', text='Start')
		self.tree.heading('venue', text='Venue')
		self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

	def refresh(self):
		for r in self.tree.get_children():
			self.tree.delete(r)
		if not self.app.current_user:
			return
		regs = self.app.db.get_registrations_by_user(self.app.current_user[0])
		for r in regs:
			self.tree.insert('', tk.END, values=(r['start'], r.get('venue_name')), iid=r['event_id'])


class OrganizerFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		ttk.Button(self, text="Create Event", command=self.create_event).pack(padx=6, pady=6)
		self.tree = ttk.Treeview(self, columns=('venue','start'), show='headings')
		self.tree.heading('venue', text='Venue')
		self.tree.heading('start', text='Start')
		self.tree.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

	def refresh(self):
		for r in self.tree.get_children():
			self.tree.delete(r)
		if not self.app.current_user:
			return
		evs = self.app.db.get_events_by_organizer(self.app.current_user[0])
		for e in evs:
			self.tree.insert('', tk.END, iid=e['id'], values=(e.get('venue_name'), e.get('start')))

	def create_event(self):
		dlg = tk.Toplevel(self)
		dlg.title('Create Event')
		ttk.Label(dlg, text='Title').grid(row=0, column=0)
		title = ttk.Entry(dlg)
		title.grid(row=0, column=1)
		ttk.Label(dlg, text='Description').grid(row=1, column=0)
		desc = ttk.Entry(dlg)
		desc.grid(row=1, column=1)
		ttk.Label(dlg, text='Venue').grid(row=2, column=0)
		venues = self.app.db.get_venues()
		vmap = {f"{v[1]} ({v[3]})": v[0] for v in venues}
		ven_combo = ttk.Combobox(dlg, values=list(vmap.keys()))
		ven_combo.grid(row=2, column=1)
		ttk.Label(dlg, text='Capacity').grid(row=3, column=0)
		cap = ttk.Entry(dlg)
		cap.grid(row=3, column=1)
		ttk.Label(dlg, text='Start (YYYY-MM-DD HH:MM)').grid(row=4, column=0)
		start = ttk.Entry(dlg)
		start.grid(row=4, column=1)

		def create():
			t = title.get().strip()
			d = desc.get().strip()
			vsel = ven_combo.get()
			v = vmap.get(vsel)
			try:
				capacity = int(cap.get())
			except Exception:
				messagebox.showerror('Error', 'Invalid capacity')
				return
			s = start.get().strip()
			if not (t and v and s):
				messagebox.showerror('Error', 'Fill required fields')
				return
			self.app.db.create_event(t, d, v, self.app.current_user[0], capacity, s)
			messagebox.showinfo('OK', 'Event created')
			dlg.destroy()
			self.refresh()

		ttk.Button(dlg, text='Create', command=create).grid(row=5, column=0, columnspan=2)


class AdminFrame(ttk.Frame):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		top = ttk.Frame(self)
		top.pack(fill=tk.X)
		ttk.Button(top, text='Manage Venues', command=self.manage_venues).pack(side=tk.LEFT, padx=4, pady=6)
		ttk.Button(top, text='Manage Users', command=self.manage_users).pack(side=tk.LEFT, padx=4)

	def manage_venues(self):
		dlg = tk.Toplevel(self)
		dlg.title('Venues')
		tree = ttk.Treeview(dlg, columns=('address','capacity'), show='headings')
		tree.heading('address', text='Address')
		tree.heading('capacity', text='Capacity')
		tree.pack(fill=tk.BOTH, expand=True)
		for v in self.app.db.get_venues():
			tree.insert('', tk.END, iid=v[0], values=(v[2], v[3]))

		def add():
			nd = tk.Toplevel(dlg)
			nd.title('Add Venue')
			ttk.Label(nd, text='Name').grid(row=0, column=0)
			n = ttk.Entry(nd)
			n.grid(row=0, column=1)
			ttk.Label(nd, text='Address').grid(row=1, column=0)
			a = ttk.Entry(nd)
			a.grid(row=1, column=1)
			ttk.Label(nd, text='Capacity').grid(row=2, column=0)
			c = ttk.Entry(nd)
			c.grid(row=2, column=1)

			def create():
				try:
					self.app.db.create_venue(n.get().strip(), a.get().strip(), int(c.get().strip()))
					messagebox.showinfo('OK','Venue added')
					nd.destroy()
					dlg.destroy()
					self.manage_venues()
				except Exception as ex:
					messagebox.showerror('Error', str(ex))

			ttk.Button(nd, text='Create', command=create).grid(row=3, column=0, columnspan=2)

		ttk.Button(dlg, text='Add Venue', command=add).pack(pady=6)

	def manage_users(self):
		dlg = tk.Toplevel(self)
		dlg.title('Users')
		tree = ttk.Treeview(dlg, columns=('email','role'), show='headings')
		tree.heading('email', text='Email')
		tree.heading('role', text='Role')
		tree.pack(fill=tk.BOTH, expand=True)
		for u in self.app.db.get_users():
			tree.insert('', tk.END, iid=u[0], values=(u[2], u[3]))

		def delete():
			sel = tree.focus()
			if not sel:
				return
			if messagebox.askyesno('Confirm','Delete user?'):
				self.app.db.delete_user(int(sel))
				dlg.destroy()
				self.manage_users()

		ttk.Button(dlg, text='Delete Selected', command=delete).pack(pady=6)


if __name__ == '__main__':
	app = EventApp()
	app.mainloop()