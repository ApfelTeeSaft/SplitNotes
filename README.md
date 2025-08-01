# SplitNotes

Cross-platform software for syncing notes with LiveSplit using the LiveSplit server component.

SplitNotes automatically shows notes for the split you are currently on, with support for Windows, macOS, and Linux.

![Screenshot 1](http://i.imgur.com/CMlF2pj.png) 
![Screenshot 2](http://i.imgur.com/4Ei2IiJ.png)

## Features

* **Cross-platform support** - Works on Windows, macOS, and Linux
* **Automatic note display** based on the active split in LiveSplit
* **Preview functionality** - Use arrow keys to preview notes when no run is active
* **Dual layout modes** - Single or double layout to show current and next split notes
* **Customizable appearance** - Adjustable fonts, colors, and window size
* **Flexible note format** - Support for custom split separators
* **Live connection status** - Visual indicator of LiveSplit connection

## System Requirements

- **Python 3.6+** (for running from source)
- **LiveSplit** with Server Component
- **Operating System**: Windows 7+, macOS 10.12+, or Linux with X11

### Platform-Specific Requirements

**Windows:**
- No additional requirements for compiled version
- For source: Python with tkinter (included in standard installation)

**macOS:**
- No additional requirements for .app bundle
- For source: Python 3 with tkinter

**Linux:**
- For compiled version: glibc 2.17+
- For source: `python3`, `python3-tk`
  ```bash
  # Ubuntu/Debian
  sudo apt install python3 python3-tk
  
  # Fedora/RHEL
  sudo dnf install python3 python3-tkinter
  
  # Arch
  sudo pacman -S python python-tkinter
  ```

## Installation

### Method 1: Download Compiled Version
1. Download the latest release for your platform from the [releases page](https://github.com/apfelteesaft/SplitNotes/releases)
2. Extract the archive
3. Run the executable (`SplitNotes.exe`, `SplitNotes.app`, or `splitnotes`)

### Method 2: Install LiveSplit Server Component
1. Download the latest version of LiveSplit Server Component from [this site](https://github.com/LiveSplit/LiveSplit.Server/releases)
2. Unzip and move the files to the component folder in your LiveSplit install (`...\LiveSplit\Components`)

### Method 3: Run from Source
1. Ensure Python 3.6+ is installed
2. Download/clone this repository
3. Create a `resources/` folder with the icon files
4. Run: `python main_window.py` (or `python3 main_window.py` on Linux/macOS)

## Usage

### Connecting to LiveSplit

1. **Launch SplitNotes**
2. **Launch LiveSplit**
3. In LiveSplit: **Edit Layout** → **+** → **Control** → **LiveSplit Server** → **OK**
4. In LiveSplit: **Control** → **Start Server**
5. SplitNotes should connect automatically (green icon = connected, red = disconnected)

### Loading Notes

**Right-click** in SplitNotes and select **"Load Notes"** to choose your text file.

### Note File Format

Notes should be stored in a text file with the following format:

#### Using Newline Separator (Default)
```
[Split 1 Title]
These are notes for the first split.
You can write multiple lines.

[Split 2 Title]  
Notes for split 2 go here.
Empty line above separates the splits.

[Split 3 Title]
Final split notes.
```

#### Using Custom Separator
```
[Split 1 Title]
Notes for split 1.
Multiple lines are fine.
-end-
[Split 2 Title]
Notes for split 2.
-end-
[Split 3 Title]
Notes for split 3.
```

**Format Rules:**
- Text in brackets `[like this]` is ignored (use for titles/comments)
- Empty lines (or custom separator) divide notes between splits
- All other text becomes part of the notes
- Encoding: UTF-8 recommended, with fallback support for other encodings

### Controls

- **Right-click**: Open context menu
- **Left/Right Arrow Keys**: Preview notes when timer is not running
- **Context Menu Options**:
  - Load Notes
  - Settings (customize appearance, layout, server port, separator)

### Settings

Access via right-click → **Settings**:

- **Font & Size**: Choose from system fonts
- **Colors**: Customize text and background colors  
- **Layout**: Single or double (shows current + next split)
- **Server Port**: Change if using non-default LiveSplit port (default: 16834)
- **Split Separator**: Use newlines or custom text to separate splits

## Platform-Specific Notes

### Windows
- Windows Defender might flag the executable initially - add an exception if needed
- Supports all Windows versions from 7 onwards

### macOS  
- First launch might require right-click → Open due to Gatekeeper security
- Supports both Intel and Apple Silicon Macs
- Integrates with system dark/light mode

### Linux
- Requires X11 display server (most desktop environments)
- Tested on Ubuntu, Fedora, and Arch Linux
- Application follows system theme where possible

## Building from Source

See `build_instructions.txt` for detailed build instructions for each platform.

**Quick Build:**
```bash
# Windows
pip install cx_Freeze
python setup_windows.py build

# macOS  
pip install py2app
python setup_mac.py py2app

# Linux
pip install cx_Freeze
python setup_linux.py build
python setup_linux.py package
```

## Troubleshooting

### Connection Issues
- Ensure LiveSplit Server component is installed and started
- Check that port 16834 is not blocked by firewall
- Verify SplitNotes and LiveSplit are on the same machine

### Display Issues
- Update graphics drivers if experiencing rendering problems
- Try different font settings if text appears corrupted
- Ensure display scaling is set appropriately

### File Loading Issues
- Verify the notes file is not corrupted or locked by another program
- Try saving the file with UTF-8 encoding
- Check file permissions (especially on Linux/macOS)

### Performance Issues
- Close unnecessary applications if SplitNotes becomes slow
- Try reducing font size or window size
- Ensure adequate system memory is available

## Development

**Language**: Python 3.6+  
**GUI Framework**: tkinter (cross-platform)  
**Architecture**: Event-driven with threaded network communication  
**License**: MIT  

**Key Files:**
- `main_window.py` - Main application and GUI
- `ls_connection.py` - LiveSplit server communication  
- `note_reader.py` - Note file parsing
- `setting_handler.py` - Configuration management
- `config.py` - Application constants and platform detection

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

MIT License - see `license.txt` for details.

## Credits

**Originally Created by**: joeloskarsson
**Ported to MacOS, Linux and refind Build Setup by**: ApfelTeeSaft
**Original Version**: Windows-only Python application  
**Cross-Platform Version**: Enhanced with macOS and Linux support

---

*For more information and updates, visit the [GitHub repository](https://github.com/apfelteesaft/SplitNotes).*