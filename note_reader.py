import tkinter.filedialog as file_dia
import os.path as path

import config

"""
NOTE STANDARD FORMATTING
empty newlines separate notes for different splits

It is also possible to set your own split separator in the settings menu

lines that start and end with [ ] are ignored for notes.
these can be used for titles. 
(ex. [Split1] is not included in notes)

all other lines of text are added as notes
"""


def get_note_lines(file_path):
	"""
	Reads file at given path and returns 
	a list containing all rows of text in given file.
	Returns false if file can not be read.
	"""

	# check so file isn't too big
	try:
		if path.getsize(file_path) > config.MAX_FILE_SIZE:
			return False
	except:
		return False

	try:
		# Try different encodings for cross-platform compatibility
		encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
		notes_file = None
		
		for encoding in encodings:
			try:
				notes_file = open(file_path, "r", encoding=encoding)
				break
			except UnicodeDecodeError:
				continue
		
		if notes_file is None:
			return False
			
	except Exception:
		return False

	# read file line per line
	f_lines = []
	try:
		with notes_file:
			for line in notes_file:
				f_lines.append(line)
	except Exception:
		return False

	return f_lines


def decode_notes(note_lines, separator):
	"""
	Takes a list containing strings.
	Encodes given strings according to the note formatting.
	Returns the list containing the notes for every split. 
	"""

	# Check if newline is being used as separator
	if separator == config.NEWLINE_CONSTANT:
		separator = ""  # left after stripping newline

	def is_title(line):
		if not line:
			return False
		stripped = line.strip()
		return stripped.startswith("[") and stripped.endswith("]")

	def is_separator(line):
		return line.strip() == separator.strip()

	def is_newline(s):
		return s.strip() == ""

	def remove_new_line(line):
		# Remove trailing newline characters
		return line.rstrip('\n\r')

	note_list = []
	cur_notes = ""

	for line in note_lines:
		line = remove_new_line(line)

		if separator == "" and is_newline(line):
			# Using newline as separator
			if cur_notes.strip():
				note_list.append(cur_notes.strip())
				cur_notes = ""
		elif separator != "" and is_separator(line):
			# Using custom separator
			if cur_notes.strip():
				note_list.append(cur_notes.strip())
				cur_notes = ""
		else:
			if not is_title(line):
				if cur_notes:
					cur_notes += "\n"
				cur_notes += line

	# Add the last notes if any
	if cur_notes.strip():
		note_list.append(cur_notes.strip())

	return note_list


def get_notes(file_path, separator):
	"""
	Takes a path to a file and returns a list with the notes 
	in the file encoded according to the note formatting.
	
	Returns False if file is empty.
	"""
	if not file_exists(file_path):
		return False
		
	note_lines = get_note_lines(file_path)

	if not note_lines:
		return False

	note_list = decode_notes(note_lines, separator)

	return note_list if note_list else False


def select_file():
	"""
	Opens a file select window.
	Returns False upon no file selection.
	Otherwise returns absolute path to selected file.
	"""
	try:
		file = file_dia.askopenfilename(
			title="Select Notes File",
			filetypes=config.TEXT_FILES
		)

		if file:
			return file
		else:
			return False
	except Exception:
		return False


def file_exists(file):
	"""Checks if given path leads to an existing file."""
	try:
		return path.isfile(file)
	except:
		return False