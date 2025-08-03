import tkinter
from tkinter import messagebox, ttk
import json
import socket
import threading
import time
import os
import sys
import platform

import config
import ls_connection as con
import note_reader as noter
import setting_handler

# Enhanced runtime info with bridge server capabilities
runtime_info = {
	"ls_connected": False,
	"timer_running": False,
	"active_split": -1,
	"notes": [],
	"server_port": 0,
	"force_reset": False,
	"double_layout": False,
	"settings": {},
	# Bridge server specific (TCP-based, no websockets)
	"bridge_enabled": False,
	"bridge_port": 16835,
	"bridge_server": None,
	"bridge_state": {}
}

root = tkinter.Tk()

# Cross-platform path handling
if getattr(sys, 'frozen', False):
	application_path = os.path.dirname(sys.executable)
else:
	application_path = os.path.dirname(os.path.realpath(__file__))

red_path = os.path.join(application_path, config.RESOURCE_FOLDER, config.ICONS["RED"])
green_path = os.path.join(application_path, config.RESOURCE_FOLDER, config.ICONS["GREEN"])

# Initialize icons
red_icon = None
green_icon = None

try:
	if os.path.exists(red_path):
		red_icon = tkinter.PhotoImage(file=red_path)
	if os.path.exists(green_path):
		green_icon = tkinter.PhotoImage(file=green_path)
except Exception as e:
	print(f"Warning: Could not load icons: {e}")


class BridgeServer:
	"""TCP-based bridge server for browser extensions (replaces websockets)"""
	
	def __init__(self, port=16835):
		self.port = port
		self.host = 'localhost'
		self.running = False
		self.server_socket = None
		self.clients = []
		self.state_lock = threading.Lock()
		
	def start(self):
		"""Start the TCP bridge server"""
		if self.running:
			return True
			
		try:
			self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server_socket.bind((self.host, self.port))
			self.server_socket.listen(5)
			
			self.running = True
			
			# Start server thread
			server_thread = threading.Thread(target=self._server_loop, daemon=True)
			server_thread.start()
			
			print(f"Bridge server started on {self.host}:{self.port}")
			return True
			
		except Exception as e:
			print(f"Failed to start bridge server: {e}")
			return False
	
	def stop(self):
		"""Stop the bridge server"""
		self.running = False
		
		# Close all client connections
		for client in self.clients[:]:
			try:
				client.close()
			except:
				pass
		self.clients.clear()
		
		# Close server socket
		if self.server_socket:
			try:
				self.server_socket.close()
			except:
				pass
		
		print("Bridge server stopped")
	
	def _server_loop(self):
		"""Main server loop for accepting connections"""
		while self.running:
			try:
				client, address = self.server_socket.accept()
				print(f"Browser client connected from {address}")
				
				self.clients.append(client)
				client_thread = threading.Thread(
					target=self._handle_client, 
					args=(client,), 
					daemon=True
				)
				client_thread.start()
				
			except Exception as e:
				if self.running:
					print(f"Error accepting connection: {e}")
	
	def _handle_client(self, client):
		"""Handle individual client connections"""
		try:
			while self.running:
				data = client.recv(1024)
				if not data:
					break
				
				try:
					# Parse JSON message from browser extension
					message = json.loads(data.decode('utf-8'))
					self._process_browser_message(message)
				except json.JSONDecodeError:
					# Handle plain text commands if needed
					command = data.decode('utf-8').strip()
					print(f"Received plain text command: {command}")
					
		except Exception as e:
			print(f"Error handling client: {e}")
		finally:
			try:
				client.close()
			except:
				pass
			if client in self.clients:
				self.clients.remove(client)
			print("Browser client disconnected")
	
	def _process_browser_message(self, message):
		"""Process JSON messages from browser extensions"""
		with self.state_lock:
			try:
				if message.get('type') == 'timer_state':
					# Update runtime info with browser state
					old_split = runtime_info["active_split"]
					old_running = runtime_info["timer_running"]
					
					runtime_info["timer_running"] = message.get('running', False)
					runtime_info["active_split"] = message.get('currentSplit', -1)
					
					# Log changes for debugging
					if old_split != runtime_info["active_split"]:
						print(f"Browser sync: Split changed {old_split} -> {runtime_info['active_split']}")
					
					if old_running != runtime_info["timer_running"]:
						print(f"Browser sync: Timer {'started' if runtime_info['timer_running'] else 'stopped'}")
					
					# Store bridge state
					runtime_info["bridge_state"] = {
						'timestamp': time.time(),
						'currentSplit': runtime_info["active_split"],
						'timerRunning': runtime_info["timer_running"],
						'splitName': message.get('splitName', ''),
						'source': 'browser'
					}
					
				elif message.get('type') == 'splits_updated':
					splits = message.get('splits', [])
					print(f"Browser sync: Received {len(splits)} split names")
					runtime_info["bridge_state"]['splits'] = splits
					
			except Exception as e:
				print(f"Error processing browser message: {e}")
	
	def send_state_to_browsers(self, state):
		"""Send current state to all connected browser clients"""
		if not self.clients:
			return
			
		message = json.dumps(state) + '\n'  # Add newline for better parsing
		disconnected_clients = []
		
		for client in self.clients:
			try:
				client.send(message.encode('utf-8'))
			except:
				disconnected_clients.append(client)
		
		# Remove disconnected clients
		for client in disconnected_clients:
			if client in self.clients:
				self.clients.remove(client)
	
	def get_status(self):
		"""Get bridge server status"""
		return {
			'running': self.running,
			'port': self.port,
			'clients': len(self.clients),
			'last_state': runtime_info.get("bridge_state", {})
		}


def update(window, com_socket, text1, text2):
	"""Enhanced update function with TCP bridge server support"""
	if runtime_info["force_reset"]:
		com_socket = reset_connection(com_socket, window, text1, text2)
		runtime_info["force_reset"] = False

	elif not runtime_info["ls_connected"]:
		# Check if we have browser state as fallback
		if runtime_info["bridge_enabled"] and runtime_info.get("bridge_state"):
			# Use browser state when LiveSplit is not connected
			bridge_state = runtime_info["bridge_state"]
			if time.time() - bridge_state.get('timestamp', 0) < 5:  # State is recent (5 seconds)
				if runtime_info["notes"]:
					update_GUI(window, com_socket, text1, text2)
		
		# Still try to connect to LiveSplit desktop
		con.ls_connect(com_socket, server_found, window, runtime_info["server_port"])
	else:
		# LiveSplit desktop is connected, use normal logic
		if runtime_info["notes"]:
			new_index = con.get_split_index(com_socket)

			if isinstance(new_index, bool):
				# Connection error
				com_socket = test_connection(com_socket, window, text1, text2)
			else:
				if new_index == -1:
					# Timer not running
					if runtime_info["timer_running"]:
						runtime_info["timer_running"] = False
						runtime_info["active_split"] = new_index
						update_GUI(window, com_socket, text1, text2)
						
						# Notify browsers of state change
						notify_browsers_state_change()
				else:
					# Timer is running
					if not runtime_info["timer_running"]:
						runtime_info["timer_running"] = True
						# Special case to fix scrolling
						if runtime_info["active_split"] == 0:
							runtime_info["active_split"] = -1

					if runtime_info["active_split"] != new_index:
						# New split, need to update
						runtime_info["active_split"] = new_index
						update_GUI(window, com_socket, text1, text2)
						
						# Notify browsers of state change
						notify_browsers_state_change()
		else:
			# Notes not yet loaded
			com_socket = test_connection(com_socket, window, text1, text2)

	# Continue main loop
	window.after(int(config.POLLING_TIME * 1000),
				 update, window, com_socket, text1, text2)


def notify_browsers_state_change():
	"""Notify browser extensions of state changes via TCP"""
	if runtime_info["bridge_enabled"] and runtime_info.get("bridge_server"):
		state = {
			'type': 'state_update',
			'currentSplit': runtime_info["active_split"],
			'timerRunning': runtime_info["timer_running"],
			'totalSplits': len(runtime_info["notes"]),
			'timestamp': time.time()
		}
		
		try:
			runtime_info["bridge_server"].send_state_to_browsers(state)
		except Exception as e:
			print(f"Error notifying browsers: {e}")


def menu_open_bridge_settings(root_wnd):
	"""Open bridge server settings dialog"""
	settings_wnd = tkinter.Toplevel(master=root_wnd)
	settings_wnd.title("Bridge Server Settings")
	settings_wnd.geometry("500x400")
	settings_wnd.resizable(False, False)
	settings_wnd.transient(root_wnd)
	settings_wnd.grab_set()
	
	# Center window
	settings_wnd.update_idletasks()
	x = (settings_wnd.winfo_screenwidth() // 2) - (500 // 2)
	y = (settings_wnd.winfo_screenheight() // 2) - (400 // 2)
	settings_wnd.geometry(f"+{x}+{y}")
	
	# Create notebook for tabs
	notebook = ttk.Notebook(settings_wnd)
	notebook.pack(fill='both', expand=True, padx=10, pady=10)
	
	# Bridge Settings Tab
	bridge_frame = ttk.Frame(notebook)
	notebook.add(bridge_frame, text="Bridge Server")
	
	# Enable bridge checkbox
	bridge_enabled_var = tkinter.BooleanVar(value=runtime_info["bridge_enabled"])
	bridge_enabled_cb = tkinter.Checkbutton(
		bridge_frame,
		text="Enable TCP Bridge Server for Browser Extensions",
		variable=bridge_enabled_var,
		font=config.GUI_FONT
	)
	bridge_enabled_cb.pack(anchor='w', padx=10, pady=10)
	
	# Port setting
	tkinter.Label(bridge_frame, text="Bridge Server Port:", font=config.GUI_FONT).pack(anchor='w', padx=10)
	port_var = tkinter.StringVar(value=str(runtime_info["bridge_port"]))
	port_entry = tkinter.Entry(bridge_frame, textvariable=port_var, font=config.GUI_FONT, width=10)
	port_entry.pack(anchor='w', padx=10, pady=5)
	
	tkinter.Label(
		bridge_frame, 
		text="Browser extensions connect to this TCP port (default: 16835)",
		font=('Arial', 9),
		fg='gray'
	).pack(anchor='w', padx=10)
	
	# Status frame
	status_frame = tkinter.LabelFrame(bridge_frame, text="Server Status", font=config.GUI_FONT)
	status_frame.pack(fill='x', padx=10, pady=20)
	
	status_text = tkinter.Text(status_frame, height=8, width=60, font=('Courier', 9))
	status_text.pack(padx=10, pady=10)
	
	def update_status():
		if runtime_info.get("bridge_server"):
			status = runtime_info["bridge_server"].get_status()
			status_info = f"""TCP Bridge Server Status:
Running: {'Yes' if status['running'] else 'No'}
Port: {status['port']}
Connected Browsers: {status['clients']}

Last State:
Current Split: {status['last_state'].get('currentSplit', 'N/A')}
Timer Running: {status['last_state'].get('timerRunning', 'N/A')}
Last Update: {time.ctime(status['last_state'].get('timestamp', 0)) if status['last_state'].get('timestamp') else 'Never'}
"""
		else:
			status_info = "TCP Bridge Server: Not Running"
		
		status_text.delete(1.0, tkinter.END)
		status_text.insert(1.0, status_info)
		
		# Schedule next update if window still exists
		try:
			if settings_wnd.winfo_exists():
				settings_wnd.after(2000, update_status)
		except:
			pass
	
	# Start status updates
	update_status()
	
	# Instructions Tab
	help_frame = ttk.Frame(notebook)
	notebook.add(help_frame, text="Setup Instructions")
	
	help_text = tkinter.Text(help_frame, wrap='word', font=('Arial', 10))
	help_text.pack(fill='both', expand=True, padx=10, pady=10)
	
	instructions = """Browser Extension Setup (TCP Bridge):

1. CHROME/CHROMIUM:
   • Go to chrome://extensions/
   • Enable Developer Mode
   • Click "Load unpacked"
   • Select the Chrome extension folder
   • Click the extension icon and enable the TCP bridge

2. FIREFOX:
   • Go to about:debugging
   • Click "This Firefox" → "Load Temporary Add-on"
   • Select manifest.json from Firefox extension folder
   • Click the extension icon and enable the TCP bridge

3. USAGE:
   • Start SplitNotes with TCP bridge enabled
   • Open https://one.livesplit.org/
   • Load your splits and start timing
   • SplitNotes will automatically sync with LiveSplit One
   • Notes will advance when you split in the browser

4. TROUBLESHOOTING:
   • Check that TCP bridge server is running (see Status tab)
   • Verify browser extension is enabled and connected
   • Ensure you're on one.livesplit.org
   • Check browser console for connection errors (F12)
   • Verify port 16835 is not blocked by firewall

TECHNICAL DETAILS:
The TCP bridge server replaces websockets with a simple TCP
connection on port 16835. Browser extensions communicate via
JSON messages over this TCP connection for better reliability
and simpler setup without external dependencies."""
	
	help_text.insert(1.0, instructions)
	help_text.config(state='disabled')
	
	# Buttons
	button_frame = tkinter.Frame(settings_wnd)
	button_frame.pack(fill='x', padx=10, pady=10)
	
	def apply_settings():
		try:
			# Validate port
			port = int(port_var.get())
			if not (1024 <= port <= 65535):
				raise ValueError("Port must be between 1024 and 65535")
			
			# Stop existing server if running
			if runtime_info.get("bridge_server"):
				runtime_info["bridge_server"].stop()
				runtime_info["bridge_server"] = None
			
			# Update settings
			runtime_info["bridge_enabled"] = bridge_enabled_var.get()
			runtime_info["bridge_port"] = port
			
			# Start server if enabled
			if runtime_info["bridge_enabled"]:
				bridge_server = BridgeServer(port)
				if bridge_server.start():
					runtime_info["bridge_server"] = bridge_server
					messagebox.showinfo("Success", "TCP Bridge server started successfully!")
				else:
					messagebox.showerror("Error", "Failed to start TCP bridge server!")
					return
			else:
				messagebox.showinfo("Info", "TCP Bridge server disabled")
			
			# Save settings
			settings = setting_handler.load_settings()
			settings["bridge_enabled"] = str(runtime_info["bridge_enabled"])
			settings["bridge_port"] = str(runtime_info["bridge_port"])
			setting_handler.save_settings(settings)
			
			settings_wnd.destroy()
			
		except ValueError as e:
			messagebox.showerror("Error", f"Invalid settings: {e}")
		except Exception as e:
			messagebox.showerror("Error", f"Failed to apply settings: {e}")
	
	def cancel_settings():
		settings_wnd.destroy()
	
	tkinter.Button(
		button_frame,
		text="Apply",
		command=apply_settings,
		font=config.GUI_FONT,
		width=10
	).pack(side='right', padx=5)
	
	tkinter.Button(
		button_frame,
		text="Cancel",
		command=cancel_settings,
		font=config.GUI_FONT,
		width=10
	).pack(side='right')


def update_GUI(window, com_socket, text1, text2):
	"""Updates all graphics according to current runtime_info"""
	index = runtime_info["active_split"]

	if index == -1:
		index = 0

	if runtime_info["timer_running"]:
		split_name = con.get_split_name(com_socket) if runtime_info["ls_connected"] else ""
	else:
		split_name = False

	if runtime_info["notes"]:
		set_title_notes(window, index, split_name)
		update_notes(text1, text2, index)
	else:
		update_title(config.DEFAULT_WINDOW["TITLE"], window)


def test_connection(com_socket, window, text1, text2):
	"""Runs a connection test to LiveSplit desktop"""
	if con.check_connection(com_socket):
		return com_socket
	else:
		return reset_connection(com_socket, window, text1, text2)


def reset_connection(com_socket, window, text1, text2):
	"""Resets LiveSplit desktop connection"""
	if runtime_info["timer_running"]:
		runtime_info["timer_running"] = False
		runtime_info["active_split"] = -1

	runtime_info["ls_connected"] = False

	update_icon(False, window)
	update_GUI(window, com_socket, text1, text2)

	con.close_socket(com_socket)
	return con.init_socket()


def server_found(window):
	"""Executes when LiveSplit desktop connection is established"""
	runtime_info["ls_connected"] = True
	update_icon(True, window)


def update_icon(active, window):
	"""Updates icon with TCP bridge server status consideration"""
	try:
		# Show green if either LiveSplit connected OR bridge has recent browser data
		bridge_active = (runtime_info["bridge_enabled"] and 
						runtime_info.get("bridge_state") and
						time.time() - runtime_info["bridge_state"].get('timestamp', 0) < 10)
		
		if (active or bridge_active) and green_icon:
			window.iconphoto(False, green_icon)
		elif red_icon:
			window.iconphoto(False, red_icon)
	except Exception:
		pass


def update_title(name, window):
	"""Sets the title with TCP bridge status if enabled"""
	title = name
	if runtime_info["bridge_enabled"] and runtime_info.get("bridge_server"):
		status = runtime_info["bridge_server"].get_status()
		if status['clients'] > 0:
			title += f" [TCP Bridge: {status['clients']} browser(s)]"
	
	window.wm_title(title)


def adjust_content(window, box1, box2):
	"""Adjusts content layout"""
	if runtime_info["double_layout"]:
		set_double_layout(window, box1, box2)
	else:
		set_single_layout(window, box1, box2)


def set_double_layout(window, box1, box2):
	"""Configures boxes for double layout"""
	runtime_info["double_layout"] = True

	w_width = window.winfo_width()
	w_height = window.winfo_height()

	box1.place(height=(w_height // 2), width=w_width)
	box2.place(height=(w_height // 2), width=w_width, y=(w_height // 2))


def set_single_layout(window, box1, box2):
	"""Configures boxes for single layout"""
	runtime_info["double_layout"] = False

	box2.place_forget()
	box1.place(height=window.winfo_height(), width=window.winfo_width())


def show_popup(event, menu):
	"""Displays popup menu"""
	try:
		menu.post(event.x_root, event.y_root)
	except Exception:
		pass


def menu_load_notes(window, text1, text2, com_socket):
	"""Menu load notes option"""
	load_notes(window, text1, text2, com_socket)


def load_notes(window, text1, text2, com_socket):
	"""Prompts user to select and load notes"""
	file = noter.select_file()

	if file:
		notes = noter.get_notes(file, runtime_info["settings"]["separator"])
		if notes:
			runtime_info["notes"] = notes

			settings = setting_handler.load_settings()
			settings["notes"] = file
			setting_handler.save_settings(settings)

			split_c = len(notes)
			show_info(("Notes Loaded",
					   f"Loaded notes with {split_c} splits."))

			if not runtime_info["timer_running"]:
				runtime_info["active_split"] = -1

			update_GUI(window, com_socket, text1, text2)

		else:
			show_info(config.ERRORS["NOTES_EMPTY"], True)


def show_info(info, warning=False):
	"""Displays info popup"""
	try:
		if warning:
			messagebox.showwarning(info[0], info[1])
		else:
			messagebox.showinfo(info[0], info[1])
	except Exception:
		print(f"Info: {info[1]}")


def update_notes(text1, text2, index):
	"""Displays notes with given index"""
	max_index = len(runtime_info["notes"]) - 1

	if index < 0:
		index = 0

	text1.config(state=tkinter.NORMAL)
	text2.config(state=tkinter.NORMAL)

	text1.delete("1.0", tkinter.END)
	text2.delete("1.0", tkinter.END)

	if index <= max_index:
		text1.insert(tkinter.END, runtime_info["notes"][index])

		if index < max_index:
			text2.insert(tkinter.END, runtime_info["notes"][index + 1])

	text1.config(state=tkinter.DISABLED)
	text2.config(state=tkinter.DISABLED)


def right_arrow(window, com_socket, text1, text2):
	"""Event handler for right arrow key"""
	change_preview(window, com_socket, text1, text2, 1)


def left_arrow(window, com_socket, text1, text2):
	"""Event handler for left arrow key"""
	change_preview(window, com_socket, text1, text2, -1)


def change_preview(window, com_socket, text1, text2, move):
	"""Changes displayed notes for preview"""
	if runtime_info["notes"] and not runtime_info["timer_running"]:
		max_index = len(runtime_info["notes"]) - 1
		index = runtime_info["active_split"]

		if index < 0:
			index = 0

		index += move

		if index > max_index:
			index = max_index
		elif index < 0:
			index = 0

		runtime_info["active_split"] = index
		update_GUI(window, com_socket, text1, text2)


def set_title_notes(window, index, split_name=False):
	"""Set window title to fit with displayed notes"""
	title = config.DEFAULT_WINDOW["TITLE"]

	disp_index = str(index + 1)  # start at 1
	title += " - " + disp_index

	if split_name:
		title += " - " + split_name

	if runtime_info["timer_running"]:
		title += " - " + config.RUNNING_ALERT

	update_title(title, window)


def menu_open_settings(root_wnd, box1, box2, text1, text2, com_socket):
	"""Opens the settings menu"""
	setting_handler.edit_settings(root_wnd,
								  lambda settings: apply_settings(settings,
																   root_wnd,
																   box1, box2,
																   text1, text2, com_socket))


def apply_settings(settings, window, box1, box2, text1, text2, com_socket):
	"""Applies settings to the application"""
	runtime_info["settings"] = settings

	# Server port change
	if runtime_info["server_port"] != int(settings["server_port"]):
		runtime_info["server_port"] = int(settings["server_port"])
		runtime_info["force_reset"] = True

	text_font = (settings["font"], int(settings["font_size"]))

	if setting_handler.decode_boolean_setting(settings["double_layout"]):
		set_double_layout(window, box1, box2)
	else:
		set_single_layout(window, box1, box2)

	text1.config(font=text_font)
	text2.config(font=text_font)
	text1.config(fg=settings["text_color"], bg=settings["background_color"])
	text2.config(fg=settings["text_color"], bg=settings["background_color"])

	old_note_length = len(runtime_info["notes"])

	if settings["notes"] and noter.file_exists(settings["notes"]):
		new_notes = noter.get_notes(settings["notes"], settings["separator"])

		if new_notes:
			runtime_info["notes"] = new_notes

			new_note_length = len(new_notes)

			if new_note_length != old_note_length:
				show_info(("Notes Loaded",
						   f"Loaded notes with {new_note_length} splits."))

				if not runtime_info["timer_running"]:
					runtime_info["active_split"] = -1

			update_GUI(window, com_socket, text1, text2)
		else:
			show_info(config.ERRORS["NOTES_EMPTY"], True)


def save_geometry_settings(width, height):
	"""Saves geometry settings"""
	settings = setting_handler.load_settings()
	settings["width"] = str(width)
	settings["height"] = str(height)
	setting_handler.save_settings(settings)


def do_on_close(root_wnd):
	"""Function called when main window is closed"""
	try:
		save_geometry_settings(root_wnd.winfo_width(), root_wnd.winfo_height())
	except:
		pass
	
	# Stop TCP bridge server
	if runtime_info.get("bridge_server"):
		runtime_info["bridge_server"].stop()
	
	root_wnd.destroy()


def init_UI(root):
	"""Initialize UI with TCP bridge server integration"""
	com_socket = con.init_socket()

	# Load Settings (including bridge settings)
	settings = setting_handler.load_settings()
	runtime_info["server_port"] = int(settings["server_port"])
	runtime_info["settings"] = settings
	
	# Load TCP bridge settings
	runtime_info["bridge_enabled"] = setting_handler.decode_boolean_setting(
		settings.get("bridge_enabled", "False")
	)
	runtime_info["bridge_port"] = int(settings.get("bridge_port", "16835"))
	
	# Start TCP bridge server if enabled
	if runtime_info["bridge_enabled"]:
		bridge_server = BridgeServer(runtime_info["bridge_port"])
		if bridge_server.start():
			runtime_info["bridge_server"] = bridge_server
			print("TCP bridge server started for browser extensions")
		else:
			print("Failed to start TCP bridge server")

	# Graphical components
	root.geometry(settings["width"] + "x" + settings["height"])
	root.minsize(300, 200)

	box1 = tkinter.Frame(root)
	box2 = tkinter.Frame(root)

	scroll1 = tkinter.Scrollbar(box1, width=config.SCROLLBAR_WIDTH)
	scroll2 = tkinter.Scrollbar(box2, width=config.SCROLLBAR_WIDTH)
	scroll1.pack(side=tkinter.RIGHT, fill=tkinter.Y)
	scroll2.pack(side=tkinter.RIGHT, fill=tkinter.Y)

	text1 = tkinter.Text(
		box1,
		yscrollcommand=scroll1.set,
		wrap=tkinter.WORD,
		cursor="arrow"
	)
	text1.insert(tkinter.END, config.DEFAULT_MSG)
	text1.config(state=tkinter.DISABLED)
	text1.pack(fill=tkinter.BOTH, expand=True)

	text2 = tkinter.Text(
		box2,
		yscrollcommand=scroll2.set,
		wrap=tkinter.WORD,
		cursor="arrow"
	)
	text2.insert(tkinter.END, config.DEFAULT_MSG)
	text2.config(state=tkinter.DISABLED)
	text2.pack(fill=tkinter.BOTH, expand=True)

	scroll1.config(command=text1.yview)
	scroll2.config(command=text2.yview)

	# Set font and color
	text_font = (settings["font"], int(settings["font_size"]))

	text1.config(font=text_font)
	text2.config(font=text_font)
	text1.config(fg=settings["text_color"], bg=settings["background_color"])
	text2.config(fg=settings["text_color"], bg=settings["background_color"])

	if setting_handler.decode_boolean_setting(settings["double_layout"]):
		set_double_layout(root, box1, box2)
	else:
		set_single_layout(root, box1, box2)

	# Create popup menu with TCP bridge settings
	popup = tkinter.Menu(root, tearoff=0)
	popup.add_command(
		label=config.MENU_OPTIONS["LOAD"],
		command=lambda: menu_load_notes(root, text1, text2, com_socket)
	)
	popup.add_command(
		label=config.MENU_OPTIONS["SETTINGS"],
		command=lambda: menu_open_settings(root, box1, box2, text1, text2, com_socket)
	)
	popup.add_separator()
	popup.add_command(
		label="TCP Bridge Settings",
		command=lambda: menu_open_bridge_settings(root)
	)

	# Set default window icon and title
	update_icon(False, root)
	update_title(config.DEFAULT_WINDOW["TITLE"], root)

	# Check if notes can be loaded from settings
	if settings["notes"] and noter.file_exists(settings["notes"]):
		notes = noter.get_notes(settings["notes"], settings["separator"])

		if notes:
			runtime_info["notes"] = notes
			update_GUI(root, com_socket, text1, text2)

	# Event binds
	root.bind("<Configure>", lambda e: adjust_content(root, box1, box2) if e.widget == root else None)
	
	# Platform-specific right-click handling
	if config.IS_MACOS:
		root.bind("<Button-2>", lambda e: show_popup(e, popup))
		root.bind("<Control-Button-1>", lambda e: show_popup(e, popup))
	else:
		root.bind("<Button-3>", lambda e: show_popup(e, popup))
	
	root.bind("<Right>", lambda e: right_arrow(root, com_socket, text1, text2))
	root.bind("<Left>", lambda e: left_arrow(root, com_socket, text1, text2))

	# Window close bind
	root.protocol("WM_DELETE_WINDOW", lambda: do_on_close(root))

	# Call update loop
	update(root, com_socket, text1, text2)


def main():
	"""Main entry point with TCP bridge server support"""
	try:
		root.title(config.DEFAULT_WINDOW["TITLE"])
		
		# Platform-specific optimizations
		if config.IS_MACOS:
			try:
				root.tk.call('tk', 'scaling', 1.0)
			except:
				pass
		
		# Initialize UI with TCP bridge server
		init_UI(root)
		
		# Start the main loop
		root.mainloop()
		
	except KeyboardInterrupt:
		print("\nApplication interrupted by user")
	except Exception as e:
		print(f"An error occurred: {e}")
		messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
	finally:
		# Clean up TCP bridge server
		if runtime_info.get("bridge_server"):
			runtime_info["bridge_server"].stop()
		try:
			root.destroy()
		except:
			pass


if __name__ == "__main__":
	main()