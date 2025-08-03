# CONFIG FILE WITH CONSTANTS - Clean version with Bridge Server Support
import platform
import os

# Livesplit connection
HOST = "localhost"
PORT = 16834

# Bridge server settings
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 16835
BRIDGE_ENABLED = False

# In network communication, time out after this time. (in seconds)
COM_TIMEOUT = 0.5

# Possible commands to send to LiveSplit
LS_COMMANDS = {
	"best_possible": "getbestpossibletime\r\n",
	"cur_split_index": "getsplitindex\r\n",
	"cur_split_name": "getcurrentsplitname\r\n"
}

# Default Window Settings
DEFAULT_WINDOW = {"TITLE": "SplitNotes"}

# Default Welcome Message
DEFAULT_MSG = "Right Click to Open Notes."

# Update time for polling livesplit and other actions (in seconds)
POLLING_TIME = 0.5

# File names and path for resources
RESOURCE_FOLDER = "resources"
ICONS = {"GREEN": "green.png", "RED": "red.png", "SETTINGS": "settings_icon.png"}
SETTINGS_FILE = "config.cfg"

# Default Scrollbar Width
SCROLLBAR_WIDTH = 16

# Popup menu options - Enhanced with bridge settings
MENU_OPTIONS = {
	"SINGLE": "Set Single Layout",
	"DOUBLE": "Set Double Layout",
	"LOAD": "Load Notes",
	"BIG": "Big Font",
	"SMALL": "Small Font",
	"SETTINGS": "Settings",
	"BRIDGE": "Bridge Settings"
}

# Error messages - Enhanced with bridge server errors
ERRORS = {
	"NOTES_EMPTY": ("Error!", "Notes empty or can't be loaded!"),
	"FONT_SIZE": ("Error!", "Invalid Font Size!"),
	"SERVER_PORT": ("Error!", "Invalid server port!"),
	"SEPARATOR": ("Error!", "Invalid split separator!"),
	"BRIDGE_PORT": ("Error!", "Invalid bridge server port!"),
	"BRIDGE_START": ("Error!", "Failed to start bridge server!"),
	"BRIDGE_CONNECTION": ("Error!", "Bridge server connection failed!")
}

# Max file size for notes
MAX_FILE_SIZE = 1000000000  # 1 Giga-Byte

# To be added to title to alert user that timer is running
RUNNING_ALERT = "RUNNING"

# Font for gui widgets
GUI_FONT = ("arial", 12)

# Files that should be displayed and opened as notes
TEXT_FILES = [
	("Text Files", ("*.txt", "*.log", "*.asc", "*.conf", "*.cfg")),
	('All', '*')
]

# Default content of config.cfg file - Enhanced with bridge settings
DEFAULT_CONFIG = """notes=
font_size=12
font=arial
text_color=#000000
background_color=#FFFFFF
double_layout=False
server_port=16834
width=400
height=300
separator=new_line
bridge_enabled=False
bridge_port=16835"""

NEWLINE_CONSTANT = "new_line"

# Required settings - Enhanced with bridge settings
REQUIRED_SETTINGS = (
	"notes",
	"font",
	"font_size",
	"text_color",
	"background_color",
	"server_port",
	"double_layout", 
	"width",
	"height",
	"separator",
	"bridge_enabled",
	"bridge_port"
)

# Settings window options
SETTINGS_WINDOW = {"TITLE": "Settings",
				   "WIDTH": 360,
				   "HEIGHT": 410,
				   "CANCEL": "Cancel",
				   "SAVE": "Save"}

# Bridge settings window options
BRIDGE_SETTINGS_WINDOW = {
	"TITLE": "Bridge Server Settings",
	"WIDTH": 500,
	"HEIGHT": 400,
	"CANCEL": "Cancel",
	"APPLY": "Apply"
}

# OPTIONS IN THE SETTINGS WINDOW
SETTINGS_OPTIONS = {"FONT": "Font",
					"FONT_SIZE": "Font Size",
					"TEXT_COLOR": "Text Color",
					"BG_COLOR": "Background Color",
					"SERVER_PORT": "LiveSplit Server port",
					"DEFAULT_SERVER_PORT": "(Default is 16834)",
					"DOUBLE_LAYOUT": "Use double layout",
					"NEW_LINE_SEPARATOR": "Newline as split separator",
					"CUSTOM_SEPARATOR": "Custom split separator"}

# Bridge server settings options
BRIDGE_OPTIONS = {
	"ENABLE_BRIDGE": "Enable Bridge Server",
	"BRIDGE_PORT": "Bridge Server Port",
	"DEFAULT_BRIDGE_PORT": "(Default is 16835)",
	"BRIDGE_STATUS": "Server Status",
	"CONNECTED_BROWSERS": "Connected Browsers",
	"LAST_UPDATE": "Last Update",
	"HELP_TEXT": """Browser Extension Setup:

1. CHROME/CHROMIUM:
   • Go to chrome://extensions/
   • Enable Developer Mode
   • Click "Load unpacked"
   • Select the Chrome extension folder

2. FIREFOX:
   • Go to about:debugging
   • Click "This Firefox" → "Load Temporary Add-on"
   • Select manifest.json from Firefox extension folder

3. USAGE:
   • Start SplitNotes with bridge enabled
   • Open https://one.livesplit.org/
   • Load your splits and start timing
   • Notes will automatically sync"""
}

# Platform-specific fonts
def get_available_fonts():
	"""Returns available fonts based on the platform."""
	system = platform.system()
	
	if system == "Darwin":  # macOS
		return ("Arial",
				"Courier New",
				"Georgia",
				"Helvetica",
				"Monaco",
				"Times New Roman",
				"Verdana",
				"SF Pro Display")
	elif system == "Linux":
		return ("Arial",
				"Courier New",
				"DejaVu Sans",
				"Liberation Sans",
				"Liberation Serif",
				"Ubuntu",
				"Times New Roman",
				"Verdana")
	else:  # Windows
		return ("arial",
				"courier new",
				"fixedsys",
				"ms sans serif",
				"ms serif",
				"system",
				"times new roman",
				"verdana")

AVAILABLE_FONTS = get_available_fonts()

# Platform-specific configurations
PLATFORM = platform.system()
IS_WINDOWS = PLATFORM == "Windows"
IS_MACOS = PLATFORM == "Darwin"
IS_LINUX = PLATFORM == "Linux"

# Default font adjustments for different platforms
if IS_MACOS:
	GUI_FONT = ("SF Pro Display", 12)
elif IS_LINUX:
	GUI_FONT = ("Ubuntu", 12)

# Bridge server specific constants
BRIDGE_SERVER_COMMANDS = {
	"GET_STATUS": "get_status",
	"GET_STATE": "get_state",
	"SET_STATE": "set_state",
	"BROWSER_CONNECT": "browser_connect",
	"BROWSER_DISCONNECT": "browser_disconnect"
}

# Bridge server status messages
BRIDGE_STATUS = {
	"STARTING": "Starting bridge server...",
	"RUNNING": "Bridge server running",
	"STOPPED": "Bridge server stopped",
	"ERROR": "Bridge server error",
	"NO_CLIENTS": "No browser clients connected",
	"CLIENT_CONNECTED": "Browser client connected",
	"CLIENT_DISCONNECTED": "Browser client disconnected"
}

# Browser extension communication protocol
BROWSER_MESSAGE_TYPES = {
	"TIMER_STATE": "timer_state",
	"SPLITS_UPDATED": "splits_updated",
	"CONNECTION_TEST": "connection_test",
	"STATUS_REQUEST": "status_request",
	"SETTINGS_UPDATE": "settings_update"
}

# Network timeouts for bridge server
BRIDGE_TIMEOUTS = {
	"CONNECTION": 5.0,  # seconds
	"READ": 1.0,        # seconds
	"KEEPALIVE": 30.0   # seconds
}

# Application info for packaging
APP_NAME = "SplitNotes"
APP_VERSION = "1.1.0"  # Incremented for bridge server support
APP_AUTHOR = "ApfelTeeSaft"
APP_DESCRIPTION = "Software for syncing notes with LiveSplit using the LiveSplit server component and browser extensions."

# Bridge server user agent for HTTP requests
BRIDGE_USER_AGENT = f"{APP_NAME}/{APP_VERSION} BridgeServer"

# Default bridge server settings for first run
DEFAULT_BRIDGE_SETTINGS = {
	"enabled": False,
	"port": BRIDGE_PORT,
	"host": BRIDGE_HOST,
	"auto_start": True,
	"log_connections": True,
	"timeout": 30
}

# Maximum number of concurrent browser connections
MAX_BROWSER_CONNECTIONS = 10

# Bridge server logging levels
BRIDGE_LOG_LEVELS = {
	"DEBUG": 0,
	"INFO": 1,
	"WARNING": 2,
	"ERROR": 3
}

# Default log level for bridge server
DEFAULT_BRIDGE_LOG_LEVEL = BRIDGE_LOG_LEVELS["INFO"]