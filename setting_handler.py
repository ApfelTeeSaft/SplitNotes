import tkinter.colorchooser as colorchooser
from tkinter import messagebox as msgbox
import tkinter
import os
import sys

import config

# Cross-platform path handling
if getattr(sys, 'frozen', False):
	# Running as compiled executable
	application_path = os.path.dirname(sys.executable)
else:
	# Running as script
	application_path = os.path.dirname(os.path.realpath(__file__))

settings_path = os.path.join(
	application_path,
	config.RESOURCE_FOLDER,
	config.SETTINGS_FILE
)

settings_icon_path = os.path.join(
	application_path,
	config.RESOURCE_FOLDER,
	config.ICONS["SETTINGS"]
)


def load_settings():
	"""
	Tries to load settings from file.
	If no working settings-file exist one is created and the default settings are returned.
	
	returns a dictionary with all settings.
	"""

	# Ensure resources directory exists
	os.makedirs(os.path.dirname(settings_path), exist_ok=True)

	# try to open default settings file
	try:
		with open(settings_path, "r", encoding='utf-8') as settings_file:
			settings_content = settings_file.readlines()
			settings_content = [line.strip() for line in settings_content]
	except:
		# File not found
		settings_content = set_default_settings()

	settings = format_settings(settings_content)

	# Check so settings file has all settings
	if not validate_settings(settings):
		settings = format_settings(set_default_settings())

	return settings


def set_default_settings():
	"""
	Creates a config file with default settings. 
	Returns the default config-file content.
	"""
	set_settings_file_content(config.DEFAULT_CONFIG)
	return config.DEFAULT_CONFIG.split("\n")


def format_settings(file_rows):
	"""
	Takes a list of settings (as written in config files) and 
	formats it to a dictionary.
	
	Returns a dictionary with all settings as keys.
	"""
	SETTING_PART_LENGTH = 2

	settings = {}

	for row in file_rows:
		row = row.strip()
		if '=' in row:
			parts = row.split("=", 1)

			if len(parts) == SETTING_PART_LENGTH:
				# Strip to remove whitespace at end and beginning
				settings[parts[0].strip()] = parts[1].strip()

	return settings


def validate_settings(settings):
	"""
	Checks a settings dictionary so that all the needed settings are present.
	"""

	for req_setting in config.REQUIRED_SETTINGS:
		if req_setting not in settings:
			return False

	if not validate_font_size(settings["font_size"]):
		return False

	if not validate_server_port(settings["server_port"]):
		return False

	if not validate_color(settings["text_color"]):
		return False

	if not validate_color(settings["background_color"]):
		return False

	if settings["font"] not in config.AVAILABLE_FONTS:
		return False

	if settings["double_layout"] not in ["True", "False"]:
		return False

	if not validate_pixels(settings["width"]):
		return False

	if not validate_pixels(settings["height"]):
		return False

	if not validate_separator(settings["separator"]):
		return False

	return True


def set_settings_file_content(content):
	"""
	Saves given content to the config file, config.cfg, in the resources directory.
	"""
	# Ensure directory exists
	os.makedirs(os.path.dirname(settings_path), exist_ok=True)
	
	try:
		with open(settings_path, "w", encoding='utf-8') as settings_file:
			settings_file.write(content)
	except Exception as e:
		print(f"Error saving settings: {e}")


def edit_settings(root_wnd, apply_method):
	"""
	Sets up a window for editing settings.
	root_wnd is the main window that settings should be applied to.
	apply_method is the method to be called to apply validated settings.
	"""
	settings_wnd = tkinter.Toplevel(master=root_wnd,
									width=config.SETTINGS_WINDOW["WIDTH"],
									height=config.SETTINGS_WINDOW["HEIGHT"])
	settings_wnd.title(config.SETTINGS_WINDOW["TITLE"])
	
	# Try to load settings icon
	try:
		if os.path.exists(settings_icon_path):
			settings_icon = tkinter.PhotoImage(file=settings_icon_path)
			settings_wnd.iconphoto(False, settings_icon)
	except:
		pass  # Icon loading failed, continue without icon

	settings = load_settings()

	settings_wnd.resizable(0, 0)
	settings_wnd.transient(root_wnd)  # Make it a dialog
	settings_wnd.grab_set()  # Make it modal

	# Center the window
	settings_wnd.geometry(f"{config.SETTINGS_WINDOW['WIDTH']}x{config.SETTINGS_WINDOW['HEIGHT']}")
	settings_wnd.update_idletasks()
	x = (settings_wnd.winfo_screenwidth() // 2) - (config.SETTINGS_WINDOW['WIDTH'] // 2)
	y = (settings_wnd.winfo_screenheight() // 2) - (config.SETTINGS_WINDOW['HEIGHT'] // 2)
	settings_wnd.geometry(f"+{x}+{y}")

	font_label = tkinter.Label(settings_wnd,
							   text=config.SETTINGS_OPTIONS["FONT"],
							   font=config.GUI_FONT)
	font_size_label = tkinter.Label(settings_wnd,
									text=config.SETTINGS_OPTIONS["FONT_SIZE"],
									font=config.GUI_FONT)
	text_color_label = tkinter.Label(settings_wnd,
									 text=config.SETTINGS_OPTIONS["TEXT_COLOR"],
									 font=config.GUI_FONT)
	bg_color_label = tkinter.Label(settings_wnd,
								   text=config.SETTINGS_OPTIONS["BG_COLOR"],
								   font=config.GUI_FONT)
	layout_label = tkinter.Label(settings_wnd,
								   text=config.SETTINGS_OPTIONS["DOUBLE_LAYOUT"],
								   font=config.GUI_FONT)
	newline_label = tkinter.Label(settings_wnd,
								   text=config.SETTINGS_OPTIONS["NEW_LINE_SEPARATOR"],
								   font=config.GUI_FONT)
	separator_label = tkinter.Label(settings_wnd,
								   text=config.SETTINGS_OPTIONS["CUSTOM_SEPARATOR"],
								   font=config.GUI_FONT)
	port_label = tkinter.Label(settings_wnd,
								   text=config.SETTINGS_OPTIONS["SERVER_PORT"],
								   font=config.GUI_FONT)
	default_port_label = tkinter.Label(settings_wnd,
								   text=config.SETTINGS_OPTIONS["DEFAULT_SERVER_PORT"],
								   font=config.GUI_FONT)

	# Font Selection
	selected_font = tkinter.StringVar(settings_wnd)
	selected_font.set(settings["font"])

	font_dropdown = tkinter.OptionMenu(settings_wnd,
									   selected_font,
									   *config.AVAILABLE_FONTS)
	font_dropdown.configure(font=config.GUI_FONT)

	# Font Size Selection
	font_size_entry = tkinter.Entry(settings_wnd, width=5, font=config.GUI_FONT)
	font_size_entry.insert(0, settings["font_size"])

	# Text Color Selection
	text_color = tkinter.Button(settings_wnd,
								width=3,
								height=1)

	if validate_color(settings["text_color"]):
		text_color.configure(background=settings["text_color"])
	else:
		text_color.configure(background="#000000")

	def text_color_selection():
		chosen_color = colorchooser.askcolor(parent=settings_wnd)
		if chosen_color[1]:
			settings["text_color"] = chosen_color[1]
			text_color.configure(background=settings["text_color"])
		settings_wnd.focus_force()

	text_color.configure(command=text_color_selection)

	# Background color Selection
	bg_color = tkinter.Button(settings_wnd,
								width=3,
								height=1)

	if validate_color(settings["background_color"]):
		bg_color.configure(background=settings["background_color"])
	else:
		bg_color.configure(background="#FFFFFF")

	def bg_color_selection():
		chosen_color = colorchooser.askcolor(parent=settings_wnd)
		if chosen_color[1]:
			settings["background_color"] = chosen_color[1]
			bg_color.configure(background=settings["background_color"])
		settings_wnd.focus_force()

	bg_color.configure(command=bg_color_selection)

	# Server port Selection
	port_entry = tkinter.Entry(settings_wnd, width=8, font=config.GUI_FONT)
	port_entry.insert(0, settings["server_port"])

	# Double Layout Selection
	double_layout = tkinter.BooleanVar()
	double_layout_btn = tkinter.Checkbutton(settings_wnd, variable=double_layout)

	if decode_boolean_setting(settings["double_layout"]):
		double_layout_btn.select()

	# Separator selection
	separator_entry = tkinter.Entry(settings_wnd, width=14, font=config.GUI_FONT)

	def set_separator_active(active):
		if active:
			separator_entry.configure(state="normal")
		else:
			separator_entry.configure(state="disabled")

	use_newline = tkinter.BooleanVar()
	newline_btn = tkinter.Checkbutton(settings_wnd,
									  variable=use_newline,
									  command=lambda: set_separator_active(not use_newline.get()))

	if settings["separator"] == config.NEWLINE_CONSTANT:
		newline_btn.select()
		set_separator_active(False)
	else:
		separator_entry.insert(0, settings["separator"])

	# Save and cancel buttons
	def control_and_save():
		errors_found = False

		settings["font"] = selected_font.get()

		chosen_font_size = font_size_entry.get()
		chosen_port = port_entry.get()

		if use_newline.get():
			chosen_separator = config.NEWLINE_CONSTANT
		else:
			chosen_separator = separator_entry.get()

		settings["double_layout"] = encode_boolean_setting(double_layout.get())

		if not validate_font_size(chosen_font_size):
			msgbox.showerror(config.ERRORS["FONT_SIZE"][0], config.ERRORS["FONT_SIZE"][1], parent=settings_wnd)
			errors_found = True
		else:
			settings["font_size"] = chosen_font_size

		if not validate_server_port(chosen_port):
			msgbox.showerror(config.ERRORS["SERVER_PORT"][0], config.ERRORS["SERVER_PORT"][1], parent=settings_wnd)
			errors_found = True
		else:
			settings["server_port"] = chosen_port

		if not validate_separator(chosen_separator):
			msgbox.showerror(config.ERRORS["SEPARATOR"][0], config.ERRORS["SEPARATOR"][1], parent=settings_wnd)
			errors_found = True
		else:
			settings["separator"] = chosen_separator

		if not errors_found:
			save_settings(settings)
			apply_method(settings)
			settings_wnd.destroy()
		else:
			settings_wnd.focus_force()

	save_btn = tkinter.Button(settings_wnd,
							  command=control_and_save,
							  text=config.SETTINGS_WINDOW["SAVE"],
							  font=config.GUI_FONT)
	cancel_btn = tkinter.Button(settings_wnd,
								command=settings_wnd.destroy,
								text=config.SETTINGS_WINDOW["CANCEL"],
								font=config.GUI_FONT)

	# Place all components
	font_label.place(x=15, y=15)
	font_size_label.place(x=15, y=55)
	text_color_label.place(x=15, y=95)
	bg_color_label.place(x=15, y=135)
	layout_label.place(x=15, y=175)
	newline_label.place(x=15, y=215)
	separator_label.place(x=15, y=240)
	port_label.place(x=15, y=280)
	default_port_label.place(x=15, y=305)

	font_dropdown.place(x=208, y=15)
	font_size_entry.place(x=210, y=55)
	text_color.place(x=210, y=95)
	bg_color.place(x=210, y=135)
	double_layout_btn.place(x=210, y=175)
	newline_btn.place(x=210, y=215)
	separator_entry.place(x=210, y=240)
	port_entry.place(x=210, y=280)

	save_btn.place(x=110, y=350)
	cancel_btn.place(x=190, y=350)

	# Handle window close
	def on_closing():
		settings_wnd.grab_release()
		settings_wnd.destroy()

	settings_wnd.protocol("WM_DELETE_WINDOW", on_closing)


def validate_color(color):
	"""
	Returns whether or not given color is valid in the hexadecimal format.
	"""
	if not isinstance(color, str):
		return False
	return len(color) == 7 and color[0] == "#" and all(c in '0123456789ABCDEFabcdef' for c in color[1:])


def validate_font_size(size):
	"""
	Returns whether or not given size is an acceptable font size.
	"""
	try:
		size = int(size)
	except:
		return False

	return 6 <= size <= 72


def validate_server_port(port):
	"""
	Returns Whether or not given port is a valid server port.
	"""
	try:
		port_num = int(port)
		return 1024 <= port_num <= 65535
	except:
		return False


def save_settings(settings):
	"""
	Saves given settings to the settings file.
	"""
	file_content = ""

	for key in settings.keys():
		file_content += key + "=" + str(settings[key]) + "\n"

	set_settings_file_content(file_content)


def decode_boolean_setting(setting):
	"""
	Decodes a boolean string of "True" or "False"
	to the correct boolean value.
	"""
	return str(setting) == "True"


def encode_boolean_setting(value):
	"""
	Encodes a boolean to the string "True" or "False".
	"""
	return "True" if value else "False"


def validate_pixels(pixels):
	"""
	Checks if given string can be used as a pixel value for height or width.
	Height or Width are assumed to never surpass 10000
	"""
	try:
		pixels = int(pixels)
	except:
		return False

	return 200 <= pixels <= 10000


def validate_separator(separator):
	"""
	Validates the separator string.
	"""
	if separator == config.NEWLINE_CONSTANT:
		return True
	return len(separator.strip()) > 0