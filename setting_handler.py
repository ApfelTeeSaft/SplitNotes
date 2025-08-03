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
		print(f"Settings loaded from: {settings_path}")
	except:
		# File not found
		print("Settings file not found, creating default settings")
		settings_content = set_default_settings()

	settings = format_settings(settings_content)

	# Check so settings file has all settings
	if not validate_settings(settings):
		print("Settings validation failed, creating default settings")
		settings = format_settings(set_default_settings())

	return settings


def set_default_settings():
	"""
	Creates a config file with default settings. 
	Returns the default config-file content.
	"""
	print(f"Creating default settings at: {settings_path}")
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
		if '=' in row and not row.startswith('#'):  # Skip comments
			parts = row.split("=", 1)

			if len(parts) == SETTING_PART_LENGTH:
				# Strip to remove whitespace at end and beginning
				key = parts[0].strip()
				value = parts[1].strip()
				settings[key] = value

	return settings


def validate_settings(settings):
	"""
	Checks a settings dictionary so that all the needed settings are present.
	Enhanced with comprehensive bridge settings validation.
	"""

	for req_setting in config.REQUIRED_SETTINGS:
		if req_setting not in settings:
			print(f"Missing required setting: {req_setting}")
			return False

	if not validate_font_size(settings["font_size"]):
		print(f"Invalid font size: {settings['font_size']}")
		return False

	if not validate_server_port(settings["server_port"]):
		print(f"Invalid server port: {settings['server_port']}")
		return False

	if not validate_color(settings["text_color"]):
		print(f"Invalid text color: {settings['text_color']}")
		return False

	if not validate_color(settings["background_color"]):
		print(f"Invalid background color: {settings['background_color']}")
		return False

	if settings["font"] not in config.AVAILABLE_FONTS:
		print(f"Invalid font: {settings['font']}")
		return False

	if settings["double_layout"].lower() not in ["true", "false"]:
		print(f"Invalid double_layout: {settings['double_layout']}")
		return False

	if not validate_pixels(settings["width"]):
		print(f"Invalid width: {settings['width']}")
		return False

	if not validate_pixels(settings["height"]):
		print(f"Invalid height: {settings['height']}")
		return False

	if not validate_separator(settings["separator"]):
		print(f"Invalid separator: {settings['separator']}")
		return False

	# Bridge settings validation
	if settings["bridge_enabled"].lower() not in ["true", "false"]:
		print(f"Invalid bridge_enabled: {settings['bridge_enabled']}")
		return False

	if not validate_bridge_port(settings["bridge_port"]):
		print(f"Invalid bridge port: {settings['bridge_port']}")
		return False

	print("All settings validated successfully")
	return True


def validate_bridge_port(port):
	"""Returns whether or not given port is a valid bridge server port."""
	try:
		port_num = int(port)
		return 1024 <= port_num <= 65535
	except:
		return False


def set_settings_file_content(content):
	"""
	Saves given content to the config file, config.cfg, in the resources directory.
	"""
	# Ensure directory exists
	os.makedirs(os.path.dirname(settings_path), exist_ok=True)
	
	try:
		with open(settings_path, "w", encoding='utf-8') as settings_file:
			settings_file.write(content)
		print(f"Settings content written to: {settings_path}")
	except Exception as e:
		print(f"Error saving settings content: {e}")


def save_settings(settings):
	"""
	Saves given settings to the settings file.
	Enhanced to ensure bridge settings are properly formatted.
	"""
	print("Saving settings...")
	
	# Ensure bridge settings are present and properly formatted
	if "bridge_enabled" not in settings:
		settings["bridge_enabled"] = "false"
	if "bridge_port" not in settings:
		settings["bridge_port"] = "16835"
	
	# Convert boolean values to lowercase strings for consistency
	if isinstance(settings.get("bridge_enabled"), bool):
		settings["bridge_enabled"] = str(settings["bridge_enabled"]).lower()
	
	file_content = ""
	
	# Write settings in a specific order for better readability
	setting_order = [
		"notes", "font", "font_size", "text_color", "background_color",
		"double_layout", "server_port", "width", "height", "separator",
		"bridge_enabled", "bridge_port"
	]
	
	# Write ordered settings first
	for key in setting_order:
		if key in settings:
			file_content += f"{key}={settings[key]}\n"
	
	# Write any additional settings not in the order list
	for key, value in settings.items():
		if key not in setting_order:
			file_content += f"{key}={value}\n"

	set_settings_file_content(file_content)
	print(f"Settings saved: bridge_enabled={settings.get('bridge_enabled')}, bridge_port={settings.get('bridge_port')}")


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

	# Create labels
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

	# Place all components with updated positions
	y_offset = 15
	font_label.place(x=15, y=y_offset)
	y_offset += 40
	font_size_label.place(x=15, y=y_offset)
	y_offset += 40
	text_color_label.place(x=15, y=y_offset)
	y_offset += 40
	bg_color_label.place(x=15, y=y_offset)
	y_offset += 40
	layout_label.place(x=15, y=y_offset)
	y_offset += 25
	newline_label.place(x=15, y=y_offset)
	y_offset += 25
	separator_label.place(x=15, y=y_offset)
	y_offset += 40
	port_label.place(x=15, y=y_offset)
	y_offset += 25
	default_port_label.place(x=15, y=y_offset)

	# Place input controls
	y_offset = 15
	font_dropdown.place(x=208, y=y_offset)
	y_offset += 40
	font_size_entry.place(x=210, y=y_offset)
	y_offset += 40
	text_color.place(x=210, y=y_offset)
	y_offset += 40
	bg_color.place(x=210, y=y_offset)
	y_offset += 40
	double_layout_btn.place(x=210, y=y_offset)
	y_offset += 25
	newline_btn.place(x=210, y=y_offset)
	y_offset += 25
	separator_entry.place(x=210, y=y_offset)
	y_offset += 40
	port_entry.place(x=210, y=y_offset)

	# Place buttons at bottom
	save_btn.place(x=110, y=450)
	cancel_btn.place(x=190, y=450)

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


def decode_boolean_setting(setting):
	"""
	Decodes a boolean string of "True" or "False"
	to the correct boolean value.
	Enhanced to handle multiple formats.
	"""
	return str(setting).lower() in ("true", "1", "yes", "on")


def encode_boolean_setting(value):
	"""
	Encodes a boolean to the string "true" or "false".
	"""
	return "true" if value else "false"


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


def debug_settings():
	"""Debug function to print current settings"""
	print("\n=== Settings Debug ===")
	try:
		settings = load_settings()
		print("Current settings:")
		for key, value in settings.items():
			print(f"  {key}: {value}")
		
		print(f"\nSettings file location: {settings_path}")
		print(f"Settings file exists: {os.path.exists(settings_path)}")
		
		if os.path.exists(settings_path):
			with open(settings_path, 'r') as f:
				content = f.read()
			print(f"\nRaw file content:\n{content}")
		
	except Exception as e:
		print(f"Error in debug_settings: {e}")
	print("=== End Settings Debug ===\n")