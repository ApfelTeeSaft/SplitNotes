import tkinter
from tkinter import messagebox

import os
import sys
import platform

import config
import ls_connection as con
import note_reader as noter
import setting_handler

runtime_info = {
	"ls_connected": False,
	"timer_running": False,
	"active_split": -1,
	"notes": [],
	"server_port": 0,
	"force_reset": False,
	"double_layout": False,
	"settings": {}
}

root = tkinter.Tk()

# Cross-platform path handling
if getattr(sys, 'frozen', False):
	# Running as compiled executable
	application_path = os.path.dirname(sys.executable)
else:
	# Running as script
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


def update(window, com_socket, text1, text2):
	"""
	Function to loop along tkinter mainloop.
	"""
	if runtime_info["force_reset"]:
		# Boolean flag to force a connection reset
		com_socket = reset_connection(com_socket, window, text1, text2)
		runtime_info["force_reset"] = False

	elif not runtime_info["ls_connected"]:
		# try connecting to ls
		con.ls_connect(com_socket, server_found, window, runtime_info["server_port"])
	else:
		# is_connected
		if runtime_info["notes"]:
			# notes loaded

			# get index of current split
			new_index = con.get_split_index(com_socket)

			if isinstance(new_index, bool):
				# Connection error
				com_socket = test_connection(com_socket, window, text1, text2)
			else:
				# index retrieved successfully
				if new_index == -1:
					# timer not running
					if runtime_info["timer_running"]:
						runtime_info["timer_running"] = False
						runtime_info["active_split"] = new_index
						update_GUI(window, com_socket, text1, text2)
				else:
					# timer is running
					if not runtime_info["timer_running"]:
						runtime_info["timer_running"] = True

						# special case to fix scrolling
						if runtime_info["active_split"] == 0:
							runtime_info["active_split"] = -1

					if not runtime_info["active_split"] == new_index:
						# new split, need to update
						runtime_info["active_split"] = new_index

						update_GUI(window, com_socket, text1, text2)
		else:
			# notes not yet loaded
			com_socket = test_connection(com_socket, window, text1, text2)

	# self looping
	window.after(int(config.POLLING_TIME * 1000),
				 update, window, com_socket, text1, text2)


def update_GUI(window, com_socket, text1, text2):
	"""
	Updates all graphics according to current runtime_info.
	Sets window title and Text-box content.
	Does NOT set window icon.
	"""
	index = runtime_info["active_split"]

	if index == -1:
		index = 0

	if runtime_info["timer_running"]:
		# Does not test connection if it fails
		split_name = con.get_split_name(com_socket)
	else:
		split_name = False

	if runtime_info["notes"]:
		set_title_notes(window, index, split_name)
		update_notes(text1, text2, index)
	else:
		update_title(config.DEFAULT_WINDOW["TITLE"], window)


def test_connection(com_socket, window, text1, text2):
	"""
	Runs a connection test to ls using given socket.
	If test is unsuccessful, resets connection.
	Returns a socket that should be used for communication with ls.
	"""
	if con.check_connection(com_socket):
		return com_socket
	else:
		return reset_connection(com_socket, window, text1, text2)


def reset_connection(com_socket, window, text1, text2):
	"""
	Resets all variables and closes given socket.
	Updates GUI to respond to connection loss.
	Returns a fresh socket that can be used to connect to ls.
	"""
	if runtime_info["timer_running"]:
		runtime_info["timer_running"] = False
		runtime_info["active_split"] = -1

	runtime_info["ls_connected"] = False

	update_icon(False, window)
	update_GUI(window, com_socket, text1, text2)

	# Close old and return a fresh socket
	con.close_socket(com_socket)

	return con.init_socket()


def server_found(window):
	"""
	Executes correct settings for when 
	ls connection has been established.
	"""
	runtime_info["ls_connected"] = True
	update_icon(True, window)


def update_icon(active, window):
	"""Updates icon of window depending on "active" variable"""
	try:
		if active and green_icon:
			window.iconphoto(False, green_icon)
		elif not active and red_icon:
			window.iconphoto(False, red_icon)
	except Exception:
		pass  # Icon update failed, continue without icon


def update_title(name, window):
	"""Sets the title of given window to name."""
	window.wm_title(name)


def adjust_content(window, box1, box2):
	"""
	Adjusts size of box1 and box2 according to 
	layout and size of window.
	"""
	if runtime_info["double_layout"]:
		set_double_layout(window, box1, box2)
	else:
		set_single_layout(window, box1, box2)


def set_double_layout(window, box1, box2):
	"""
	Configures boxes in the window to fit as in double layout.
	"""
	runtime_info["double_layout"] = True

	w_width = window.winfo_width()
	w_height = window.winfo_height()

	box1.place(height=(w_height // 2), width=w_width)
	box2.place(height=(w_height // 2), width=w_width, y=(w_height // 2))


def set_single_layout(window, box1, box2):
	"""
	Configures boxes in the window to fit as in single layout.
	"""
	runtime_info["double_layout"] = False

	box2.place_forget()
	box1.place(height=window.winfo_height(), width=window.winfo_width())


def show_popup(event, menu):
	"""Displays given popup menu at cursor position."""
	try:
		menu.post(event.x_root, event.y_root)
	except Exception:
		pass


def menu_load_notes(window, text1, text2, com_socket):
	"""Menu selected load notes option."""
	load_notes(window, text1, text2, com_socket)


def load_notes(window, text1, text2, com_socket):
	"""
	Prompts user to select notes and then tries to load these into the UI.
	"""
	file = noter.select_file()

	if file:
		notes = noter.get_notes(file, runtime_info["settings"]["separator"])
		if notes:
			# Notes loaded correctly
			runtime_info["notes"] = notes

			# Save notes to settings
			settings = setting_handler.load_settings()
			settings["notes"] = file
			setting_handler.save_settings(settings)

			split_c = len(notes)
			show_info(("Notes Loaded",
					   ("Loaded notes with " + str(split_c) + " splits.")))

			if not runtime_info["timer_running"]:
				runtime_info["active_split"] = -1

			update_GUI(window, com_socket, text1, text2)

		else:
			show_info(config.ERRORS["NOTES_EMPTY"], True)


def show_info(info, warning=False):
	"""
	Displays an info popup window.
	if warning is True window has a warning triangle.
	"""
	try:
		if warning:
			messagebox.showwarning(info[0], info[1])
		else:
			messagebox.showinfo(info[0], info[1])
	except Exception:
		print(f"Info: {info[1]}")


def update_notes(text1, text2, index):
	"""
	Displays notes with the given index in given text widgets.
	If index is lower than 0, displays notes for index 0.
	If index is higher than the highest index there are 
	notes for the text widgets are left empty.
	
	text2 is always given the notes at index (index + 1) if existing
	"""
	max_index = (len(runtime_info["notes"]) - 1)

	if index < 0:
		index = 0

	text1.config(state=tkinter.NORMAL)
	text2.config(state=tkinter.NORMAL)

	text1.delete("1.0", tkinter.END)
	text2.delete("1.0", tkinter.END)

	if index <= max_index:
		text1.insert(tkinter.END, runtime_info["notes"][index])

		# can't display notes for index+1
		if index < max_index:
			text2.insert(tkinter.END, runtime_info["notes"][index + 1])

	text1.config(state=tkinter.DISABLED)
	text2.config(state=tkinter.DISABLED)


def right_arrow(window, com_socket, text1, text2):
	"""Event handler for right arrow key."""
	change_preview(window, com_socket, text1, text2, 1)


def left_arrow(window, com_socket, text1, text2):
	"""Event handler for left arrow key."""
	change_preview(window, com_socket, text1, text2, -1)


def change_preview(window, com_socket, text1, text2, move):
	"""
	Changes notes that are currently displayed.
	Move is either 1 for next or -1 for previous.
	"""
	if runtime_info["notes"] and (not runtime_info["timer_running"]):
		max_index = (len(runtime_info["notes"]) - 1)
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
	"""
	Set window title to fit with displayed notes.
	"""
	title = config.DEFAULT_WINDOW["TITLE"]

	disp_index = str(index + 1)  # start at 1
	title += " - " + disp_index

	if split_name:
		title += " - " + split_name

	if runtime_info["timer_running"]:
		title += " - " + config.RUNNING_ALERT

	update_title(title, window)


def menu_open_settings(root_wnd, box1, box2, text1, text2, com_socket):
	"""
	Opens the settings menu.
	"""
	setting_handler.edit_settings(root_wnd,
								  lambda settings: apply_settings(settings,
																   root_wnd,
																   box1, box2,
																   text1, text2, com_socket))


def apply_settings(settings, window, box1, box2, text1, text2, com_socket):
	"""
	Applies the given settings to the given components.
	Settings must be a correctly formatted dictionary.
	"""
	runtime_info["settings"] = settings

	# Server port change
	if not (runtime_info["server_port"] == int(settings["server_port"])):
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
			# Notes loaded correctly
			runtime_info["notes"] = new_notes

			new_note_length = len(new_notes)

			if not (new_note_length == old_note_length):
				show_info(("Notes Loaded",
						   ("Loaded notes with " + str(new_note_length) + " splits.")))

				if not runtime_info["timer_running"]:
					runtime_info["active_split"] = -1

			update_GUI(window, com_socket, text1, text2)
		else:
			show_info(config.ERRORS["NOTES_EMPTY"], True)


def save_geometry_settings(width, height):
	"""
	Saves given width and height to settings file.
	"""
	settings = setting_handler.load_settings()
	settings["width"] = str(width)
	settings["height"] = str(height)
	setting_handler.save_settings(settings)


def do_on_close(root_wnd):
	"""
	Function that is called when the main tk window is closed.
	Saves root_wnd's width and height to the settings file and
	then closes the window.
	"""
	try:
		save_geometry_settings(root_wnd.winfo_width(), root_wnd.winfo_height())
	except:
		pass
	root_wnd.destroy()


def init_UI(root):
	"""Draws default UI and creates event bindings."""

	# Create communication socket
	com_socket = con.init_socket()

	# Load Settings
	settings = setting_handler.load_settings()
	runtime_info["server_port"] = int(settings["server_port"])
	runtime_info["settings"] = settings

	# Graphical components
	root.geometry(settings["width"] + "x" + settings["height"])

	# Set minimum window size
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

	# Set font and color for text
	text_font = (settings["font"], int(settings["font_size"]))

	text1.config(font=text_font)
	text2.config(font=text_font)
	text1.config(fg=settings["text_color"], bg=settings["background_color"])
	text2.config(fg=settings["text_color"], bg=settings["background_color"])

	if setting_handler.decode_boolean_setting(settings["double_layout"]):
		set_double_layout(root, box1, box2)
	else:
		set_single_layout(root, box1, box2)

	# create popup menu
	popup = tkinter.Menu(root, tearoff=0)
	popup.add_command(
		label=config.MENU_OPTIONS["LOAD"],
		command=lambda: menu_load_notes(root, text1, text2, com_socket)
	)
	popup.add_command(
		label=config.MENU_OPTIONS["SETTINGS"],
		command=lambda: menu_open_settings(root, box1, box2, text1, text2, com_socket)
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

	# call update loop
	update(root, com_socket, text1, text2)


def main():
	"""Main entry point for the application."""
	try:
		# Set up the main window
		root.title(config.DEFAULT_WINDOW["TITLE"])
		
		# Platform-specific optimizations
		if config.IS_MACOS:
			# Use native look on macOS
			try:
				root.tk.call('tk', 'scaling', 1.0)
			except:
				pass
		
		# Initialize UI
		init_UI(root)
		
		# Start the main loop
		root.mainloop()
		
	except KeyboardInterrupt:
		print("\nApplication interrupted by user")
	except Exception as e:
		print(f"An error occurred: {e}")
		messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
	finally:
		try:
			root.destroy()
		except:
			pass


if __name__ == "__main__":
	main()