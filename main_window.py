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
		self.server_thread = None
		
	def start(self):
		"""Start the TCP bridge server"""
		if self.running:
			return True
			
		try:
			self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server_socket.settimeout(1.0)  # Add timeout for clean shutdown
			self.server_socket.bind((self.host, self.port))
			self.server_socket.listen(5)
			
			self.running = True
			
			# Start server thread
			self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
			self.server_thread.start()
			
			print(f"Bridge server started on {self.host}:{self.port}")
			return True
			
		except Exception as e:
			print(f"Failed to start bridge server: {e}")
			self.running = False
			if self.server_socket:
				try:
					self.server_socket.close()
				except:
					pass
				self.server_socket = None
			return False
	
	def stop(self):
		"""Stop the bridge server"""
		self.running = False
		
		# Close all client connections
		for client in self.clients[:]:  # Copy list to avoid modification during iteration
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
			self.server_socket = None
		
		# Wait for server thread to finish
		if self.server_thread and self.server_thread.is_alive():
			self.server_thread.join(timeout=2.0)
		
		print("Bridge server stopped")
	
	def _server_loop(self):
		"""Main server loop for accepting connections"""
		while self.running:
			try:
				client, address = self.server_socket.accept()
				print(f"Browser client connected from {address}")
				
				# Set client timeout
				client.settimeout(30.0)
				
				self.clients.append(client)
				client_thread = threading.Thread(
					target=self._handle_client, 
					args=(client, address), 
					daemon=True
				)
				client_thread.start()
				
			except socket.timeout:
				continue  # Normal timeout, check if still running
			except Exception as e:
				if self.running:
					print(f"Error accepting connection: {e}")
				break
	
	def _handle_client(self, client, address):
		"""Handle individual client connections"""
		try:
			while self.running:
				try:
					data = client.recv(1024)
					if not data:
						break
					
					try:
						# Parse JSON message from browser extension
						message = json.loads(data.decode('utf-8'))
						self._process_browser_message(message)
						
						# Send acknowledgment
						response = {"status": "ok", "timestamp": time.time()}
						client.send((json.dumps(response) + '\n').encode('utf-8'))
						
					except json.JSONDecodeError:
						# Handle plain text commands if needed
						command = data.decode('utf-8').strip()
						print(f"Received plain text command: {command}")
						
				except socket.timeout:
					continue
				except Exception as e:
					print(f"Error receiving from client {address}: {e}")
					break
					
		except Exception as e:
			print(f"Error handling client {address}: {e}")
		finally:
			try:
				client.close()
			except:
				pass
			if client in self.clients:
				self.clients.remove(client)
			print(f"Browser client {address} disconnected")
	
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
					if 'bridge_state' not in runtime_info:
						runtime_info["bridge_state"] = {}
					runtime_info["bridge_state"]['splits'] = splits
					
			except Exception as e:
				print(f"Error processing browser message: {e}")
	
	def send_state_to_browsers(self, state):
		"""Send current state to all connected browser clients"""
		if not self.clients:
			return
			
		message = json.dumps(state) + '\n'
		disconnected_clients = []
		
		for client in self.clients[:]:  # Copy list to avoid modification during iteration
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


def menu_open_bridge_settings(root_wnd):
	"""Open bridge server settings dialog with proper save button functionality"""
	settings_wnd = tkinter.Toplevel(master=root_wnd)
	settings_wnd.title("TCP Bridge Server Settings")
	settings_wnd.geometry("520x500")
	settings_wnd.resizable(False, False)
	settings_wnd.transient(root_wnd)
	settings_wnd.grab_set()
	
	# Center window
	settings_wnd.update_idletasks()
	x = (settings_wnd.winfo_screenwidth() // 2) - (520 // 2)
	y = (settings_wnd.winfo_screenheight() // 2) - (500 // 2)
	settings_wnd.geometry(f"+{x}+{y}")
	
	# Main container
	main_frame = tkinter.Frame(settings_wnd)
	main_frame.pack(fill='both', expand=True, padx=10, pady=10)
	
	# Settings section
	settings_section = tkinter.LabelFrame(main_frame, text="Bridge Configuration", font=config.GUI_FONT)
	settings_section.pack(fill='x', pady=(0, 10))
	
	# Load current settings from config file
	current_settings = setting_handler.load_settings()
	current_enabled = current_settings.get("bridge_enabled", "false").lower() == "true"
	current_port = int(current_settings.get("bridge_port", "16835"))
	
	# Enable bridge checkbox
	bridge_enabled_var = tkinter.BooleanVar(value=current_enabled)
	bridge_enabled_cb = tkinter.Checkbutton(
		settings_section,
		text="Enable TCP Bridge Server for Browser Extensions",
		variable=bridge_enabled_var,
		font=config.GUI_FONT
	)
	bridge_enabled_cb.pack(anchor='w', padx=15, pady=10)
	
	# Port setting frame
	port_frame = tkinter.Frame(settings_section)
	port_frame.pack(fill='x', padx=15, pady=5)
	
	tkinter.Label(port_frame, text="Bridge Server Port:", font=config.GUI_FONT).pack(side='left')
	
	port_var = tkinter.StringVar(value=str(current_port))
	port_entry = tkinter.Entry(port_frame, textvariable=port_var, font=config.GUI_FONT, width=8)
	port_entry.pack(side='left', padx=(10, 5))
	
	tkinter.Label(
		port_frame, 
		text="(default: 16835)",
		font=('Arial', 9),
		fg='gray'
	).pack(side='left')
	
	# Help text
	help_label = tkinter.Label(
		settings_section,
		text="Browser extensions connect to this TCP port to sync with LiveSplit One",
		font=('Arial', 9),
		fg='gray',
		wraplength=450
	)
	help_label.pack(anchor='w', padx=15, pady=(0, 10))
	
	# Save button and feedback area
	save_frame = tkinter.Frame(settings_section)
	save_frame.pack(fill='x', padx=15, pady=10)
	
	# Feedback text area
	feedback_var = tkinter.StringVar(value="")
	feedback_label = tkinter.Label(
		save_frame,
		textvariable=feedback_var,
		font=('Arial', 10),
		fg='blue',
		wraplength=300,
		justify='left'
	)
	feedback_label.pack(side='left', fill='x', expand=True)
	
	def save_bridge_settings():
		"""Save bridge settings and start/stop server based on checkbox"""
		try:
			# Clear previous feedback
			feedback_var.set("Saving settings...")
			feedback_label.config(fg='blue')
			settings_wnd.update()
			
			# Validate port
			try:
				port = int(port_var.get())
				if not (1024 <= port <= 65535):
					raise ValueError("Port must be between 1024 and 65535")
			except ValueError as e:
				feedback_var.set(f"Error: {e}")
				feedback_label.config(fg='red')
				return
			
			# Get checkbox state
			is_enabled = bridge_enabled_var.get()
			
			print(f"Saving bridge settings: enabled={is_enabled}, port={port}")
			
			# Stop existing server if running
			if runtime_info.get("bridge_server"):
				print("Stopping existing bridge server...")
				runtime_info["bridge_server"].stop()
				runtime_info["bridge_server"] = None
			
			# Update runtime settings
			runtime_info["bridge_enabled"] = is_enabled
			runtime_info["bridge_port"] = port
			
			# Save to configuration file
			settings = setting_handler.load_settings()
			settings["bridge_enabled"] = "true" if is_enabled else "false"
			settings["bridge_port"] = str(port)
			setting_handler.save_settings(settings)
			
			print(f"Settings saved to config file: bridge_enabled={settings['bridge_enabled']}")
			
			# Start or stop server based on checkbox state
			if is_enabled:
				print(f"Starting TCP bridge server on port {port}...")
				bridge_server = BridgeServer(port)
				if bridge_server.start():
					runtime_info["bridge_server"] = bridge_server
					feedback_var.set(f"✓ Settings saved! TCP Bridge server started on port {port}")
					feedback_label.config(fg='green')
					print("✓ Bridge server started successfully")
				else:
					# Failed to start server, disable the setting
					runtime_info["bridge_enabled"] = False
					settings["bridge_enabled"] = "false"
					setting_handler.save_settings(settings)
					bridge_enabled_var.set(False)  # Update checkbox
					
					feedback_var.set(f"✗ Failed to start server on port {port}. Settings disabled.")
					feedback_label.config(fg='red')
					print("✗ Failed to start bridge server")
			else:
				feedback_var.set("✓ Settings saved! TCP Bridge server disabled")
				feedback_label.config(fg='orange')
				print("✓ Bridge server disabled")
			
			# Update main window title to reflect bridge status
			try:
				update_title(config.DEFAULT_WINDOW["TITLE"], root_wnd)
			except:
				pass
				
		except Exception as e:
			feedback_var.set(f"✗ Error saving settings: {e}")
			feedback_label.config(fg='red')
			print(f"Error in save_bridge_settings: {e}")
	
	# Save button
	save_button = tkinter.Button(
		save_frame,
		text="Save Settings",
		command=save_bridge_settings,
		font=config.GUI_FONT,
		width=12,
		bg='lightblue',
		relief='raised'
	)
	save_button.pack(side='right', padx=(10, 0))
	
	# Status section
	status_frame = tkinter.LabelFrame(main_frame, text="Server Status", font=config.GUI_FONT)
	status_frame.pack(fill='both', expand=True, pady=(0, 10))
	
	# Status text area with scrollbar
	status_text_frame = tkinter.Frame(status_frame)
	status_text_frame.pack(fill='both', expand=True, padx=10, pady=10)
	
	status_text = tkinter.Text(
		status_text_frame, 
		height=8, 
		width=60, 
		font=('Courier', 9), 
		state='disabled',
		wrap='word'
	)
	status_scrollbar = tkinter.Scrollbar(status_text_frame, command=status_text.yview)
	status_text.config(yscrollcommand=status_scrollbar.set)
	
	status_text.pack(side='left', fill='both', expand=True)
	status_scrollbar.pack(side='right', fill='y')
	
	def update_status():
		"""Update the status display"""
		status_text.config(state='normal')
		status_text.delete(1.0, tkinter.END)
		
		# Get current runtime status
		bridge_server = runtime_info.get("bridge_server")
		bridge_enabled = runtime_info.get("bridge_enabled", False)
		bridge_port = runtime_info.get("bridge_port", 16835)
		
		if bridge_server and bridge_enabled:
			status = bridge_server.get_status()
			last_state = status.get('last_state', {})
			
			status_info = f"""TCP Bridge Server Status: RUNNING ✓
Port: {status['port']}
Connected Browsers: {status['clients']}
Server Running: {status['running']}

Runtime Information:
Bridge Enabled: {bridge_enabled}
Current Split: {last_state.get('currentSplit', 'N/A')}
Timer Running: {last_state.get('timerRunning', 'N/A')}
Last Update: {time.ctime(last_state.get('timestamp', 0)) if last_state.get('timestamp') else 'Never'}

Configuration Status:
Settings file: resources/config.cfg
bridge_enabled: {"true" if bridge_enabled else "false"}
bridge_port: {bridge_port}

Connection Info:
Browser extensions can connect to localhost:{bridge_port}
Send JSON messages with timer state data"""
		else:
			status_info = f"""TCP Bridge Server Status: STOPPED ✗
Port: {bridge_port}
Connected Browsers: 0
Server Running: False

Runtime Information:
Bridge Enabled: {bridge_enabled}
Current Split: N/A
Timer Running: N/A
Last Update: Never

Configuration Status:
Settings file: resources/config.cfg
bridge_enabled: {"true" if bridge_enabled else "false"}
bridge_port: {bridge_port}

To enable:
1. Check 'Enable TCP Bridge Server' checkbox above
2. Click 'Save Settings' button
3. Verify status changes to 'RUNNING ✓'"""
		
		status_text.insert(1.0, status_info)
		status_text.config(state='disabled')
		
		# Schedule next update if window still exists
		try:
			if settings_wnd.winfo_exists():
				settings_wnd.after(2000, update_status)
		except:
			pass
	
	# Start status updates
	update_status()
	
	# Test connection button
	test_frame = tkinter.Frame(main_frame)
	test_frame.pack(fill='x', pady=(0, 10))
	
	test_feedback_var = tkinter.StringVar(value="")
	test_feedback_label = tkinter.Label(
		test_frame,
		textvariable=test_feedback_var,
		font=('Arial', 9),
		fg='gray'
	)
	test_feedback_label.pack(side='left', fill='x', expand=True)
	
	def test_connection():
		"""Test the bridge server connection"""
		test_feedback_var.set("Testing connection...")
		test_feedback_label.config(fg='blue')
		settings_wnd.update()
		
		try:
			port = int(port_var.get())
		except ValueError:
			test_feedback_var.set("✗ Invalid port number")
			test_feedback_label.config(fg='red')
			return
		
		try:
			# Try to connect to the bridge server
			test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			test_socket.settimeout(3.0)
			test_socket.connect(('localhost', port))
			
			# Send test message
			test_message = {
				"type": "connection_test", 
				"timestamp": time.time(),
				"source": "settings_dialog"
			}
			test_socket.send((json.dumps(test_message) + '\n').encode('utf-8'))
			
			# Wait for response
			response = test_socket.recv(1024)
			test_socket.close()
			
			if response:
				test_feedback_var.set("✓ Connection test successful! Server is responding.")
				test_feedback_label.config(fg='green')
			else:
				test_feedback_var.set("✗ Connected but no response received")
				test_feedback_label.config(fg='orange')
				
		except ConnectionRefusedError:
			test_feedback_var.set("✗ Connection refused. Server not running.")
			test_feedback_label.config(fg='red')
		except socket.timeout:
			test_feedback_var.set("✗ Connection timeout. Check if server is running.")
			test_feedback_label.config(fg='red')
		except Exception as e:
			test_feedback_var.set(f"✗ Connection test failed: {e}")
			test_feedback_label.config(fg='red')
	
	test_button = tkinter.Button(
		test_frame,
		text="Test Connection",
		command=test_connection,
		font=config.GUI_FONT,
		width=15
	)
	test_button.pack(side='right')
	
	# Bottom buttons frame
	button_frame = tkinter.Frame(main_frame)
	button_frame.pack(fill='x')
	
	def close_dialog():
		"""Close the dialog"""
		settings_wnd.destroy()
	
	# Close button
	tkinter.Button(
		button_frame,
		text="Close",
		command=close_dialog,
		font=config.GUI_FONT,
		width=10
	).pack(side='right')
	
	# Info button for help
	def show_help():
		"""Show help information"""
		help_text = """TCP Bridge Server Help:

The TCP Bridge Server allows browser extensions to connect to SplitNotes and send timer state information from LiveSplit One.

SETUP:
1. Check 'Enable TCP Bridge Server' checkbox
2. Set the port (default: 16835)
3. Click 'Save Settings'
4. Verify status shows 'RUNNING ✓'

BROWSER EXTENSION:
Browser extensions should connect to localhost:16835 and send JSON messages like:
{
  "type": "timer_state",
  "running": true,
  "currentSplit": 2,
  "splitName": "Split Name"
}

TROUBLESHOOTING:
• Make sure port is not blocked by firewall
• Check that no other application is using the port
• Use 'Test Connection' to verify server is working
• Restart SplitNotes if server fails to start"""
		
		messagebox.showinfo("TCP Bridge Help", help_text)
	
	tkinter.Button(
		button_frame,
		text="Help",
		command=show_help,
		font=config.GUI_FONT,
		width=10
	).pack(side='right', padx=(0, 10))
	
	# Handle window close
	def on_closing():
		settings_wnd.grab_release()
		settings_wnd.destroy()

	settings_wnd.protocol("WM_DELETE_WINDOW", on_closing)
	
	# Initial feedback
	if current_enabled:
		if runtime_info.get("bridge_server"):
			feedback_var.set(f"✓ TCP Bridge server is currently running on port {current_port}")
			feedback_label.config(fg='green')
		else:
			feedback_var.set(f"⚠ Bridge enabled in config but server not running")
			feedback_label.config(fg='orange')
	else:
		feedback_var.set("TCP Bridge server is currently disabled")
		feedback_label.config(fg='gray')


def update(window, com_socket, text1, text2):
	"""Enhanced update function with TCP bridge server support"""
	if runtime_info["force_reset"]:
		com_socket = reset_connection(com_socket, window, text1, text2)
		runtime_info["force_reset"] = False

	elif not runtime_info["ls_connected"]:
		# Check if we have browser state as fallback
		if runtime_info["bridge_enabled"] and runtime_info.get("bridge_state"):
			bridge_state = runtime_info["bridge_state"]
			if time.time() - bridge_state.get('timestamp', 0) < 5:
				if runtime_info["notes"]:
					update_GUI(window, com_socket, text1, text2)
		
		# Still try to connect to LiveSplit desktop
		con.ls_connect(com_socket, server_found, window, runtime_info["server_port"])
	else:
		# LiveSplit desktop is connected, use normal logic
		if runtime_info["notes"]:
			new_index = con.get_split_index(com_socket)

			if isinstance(new_index, bool):
				com_socket = test_connection(com_socket, window, text1, text2)
			else:
				if new_index == -1:
					if runtime_info["timer_running"]:
						runtime_info["timer_running"] = False
						runtime_info["active_split"] = new_index
						update_GUI(window, com_socket, text1, text2)
						notify_browsers_state_change()
				else:
					if not runtime_info["timer_running"]:
						runtime_info["timer_running"] = True
						if runtime_info["active_split"] == 0:
							runtime_info["active_split"] = -1

					if runtime_info["active_split"] != new_index:
						runtime_info["active_split"] = new_index
						update_GUI(window, com_socket, text1, text2)
						notify_browsers_state_change()
		else:
			com_socket = test_connection(com_socket, window, text1, text2)

	window.after(int(config.POLLING_TIME * 1000), update, window, com_socket, text1, text2)


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
			show_info(("Notes Loaded", f"Loaded notes with {split_c} splits."))

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

	disp_index = str(index + 1)
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
	"""Initialize UI with proper TCP bridge server integration"""
	com_socket = con.init_socket()

	# Load Settings (including bridge settings)
	print("Loading SplitNotes settings...")
	settings = setting_handler.load_settings()
	runtime_info["server_port"] = int(settings["server_port"])
	runtime_info["settings"] = settings
	
	# Load TCP bridge settings with proper validation
	print("Loading TCP bridge settings...")
	bridge_enabled_str = settings.get("bridge_enabled", "false").lower().strip()
	runtime_info["bridge_enabled"] = bridge_enabled_str == "true"
	
	try:
		runtime_info["bridge_port"] = int(settings.get("bridge_port", "16835"))
	except (ValueError, TypeError):
		print("Invalid bridge port in settings, using default 16835")
		runtime_info["bridge_port"] = 16835
		# Update settings with correct port
		settings["bridge_port"] = "16835"
		setting_handler.save_settings(settings)
	
	print(f"Bridge settings loaded: enabled={runtime_info['bridge_enabled']}, port={runtime_info['bridge_port']}")
	
	# Start TCP bridge server if enabled in settings
	if runtime_info["bridge_enabled"]:
		print(f"Bridge is enabled in config, starting TCP bridge server on port {runtime_info['bridge_port']}...")
		bridge_server = BridgeServer(runtime_info["bridge_port"])
		if bridge_server.start():
			runtime_info["bridge_server"] = bridge_server
			print("✓ TCP bridge server started successfully for browser extensions")
		else:
			print("✗ Failed to start TCP bridge server")
			print("  This might be due to port already in use or firewall settings")
			# Don't disable the setting here - let user handle it in settings dialog
	else:
		print("TCP bridge server is disabled in configuration")

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
	
	# Debug: Print final bridge status
	bridge_running = runtime_info.get('bridge_server') is not None
	print(f"Final bridge status: enabled={runtime_info['bridge_enabled']}, server_running={bridge_running}")
	
	if runtime_info['bridge_enabled'] and not bridge_running:
		print("Warning: Bridge is enabled but server failed to start. Check TCP Bridge Settings.")


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