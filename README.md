# MKV Track Renamer

A PyQt5 application for batch renaming MKV track headers and editing track properties.

## Features

- **Batch processing**: Analyze and modify multiple MKV files at once
- **Track analysis**: Extract detailed information about video, audio, and subtitle tracks
- **Customizable naming**: Configure naming rules for different track types
- **Visual preview**: See proposed changes before applying them
- **Track flags**: Set default and forced flags for tracks
- **Language support**: Comprehensive language and codec mappings
- **Backup support**: Automatic backup creation before modifications
- **File management**: Exclude/include files from processing

## Requirements

- **Python 3.7+**
- **PyQt5** (install via `pip install PyQt5`)
- **MKVToolNix** (required for MKV file operations)

### Installing MKVToolNix

- **Windows**: Download from [mkvtoolnix.download](https://mkvtoolnix.download/)
- **macOS**: `brew install mkvtoolnix`
- **Ubuntu/Debian**: `sudo apt install mkvtoolnix`
- **CentOS/RHEL**: `sudo yum install mkvtoolnix`

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Project Structure

```
mkv_header/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── src/                    # Source code
    ├── __init__.py
    ├── config/             # Configuration management
    │   ├── __init__.py
    │   └── config_manager.py
    ├── core/               # Core functionality
    │   ├── __init__.py
    │   ├── mkv_analyzer.py
    │   ├── mkv_editor.py
    │   └── naming_rules.py
    ├── ui/                 # User interface
    │   ├── __init__.py
    │   ├── main_window.py
    │   ├── processing_thread.py
    │   └── rules_config_widget.py
    └── utils/              # Utilities
        ├── __init__.py
        └── mkv_tools_checker.py
```

## Usage

1. **Add files**: Click "Add MKV files" to select your MKV files
2. **Analyze**: Click "Analyze files" to examine track information
3. **Configure rules**: Set up naming rules in the "Naming rules" tab
4. **Preview changes**: Generate and review proposed changes in the "Preview changes" tab
5. **Apply**: Apply the changes in the "Apply changes" tab

### Tips

- **File management**: Right-click files to exclude/include or remove them
- **Track editing**: Edit track names, languages, and flags directly in the preview table
- **Auto-sync**: Video track names automatically sync with file titles inside the MKV file
- **Forced flags**: Toggle forced flags to auto-update subtitle names
- **Color Coding**: Files are color-coded in the preview for easy identification

## Architecture

- **Configuration Layer**: Manages application settings and mappings
- **Core Layer**: Handles MKV file analysis, editing, and naming rules
- **UI Layer**: Provides the PyQt5 user interface components
- **Utilities**: Helper functions and tool checking

### Key Classes

- `ConfigManager`: Manages language and codec mappings
- `MKVAnalyzer`: Analyzes MKV files using mkvmerge
- `MKVEditor`: Edits MKV files using mkvpropedit
- `NamingRules`: Generates track names based on rules
- `MainWindow`: Main application window and UI logic
- `ProcessingThread`: Background file processing
- `RulesConfigWidget`: UI for configuring naming rules

## Configuration

The application includes predefined mappings for languages, video/audio codecs and subtitle formats.


## License

MIT License