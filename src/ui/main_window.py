"""
Main application window
"""

import sys
import os
from pathlib import Path
from typing import Dict, Tuple, List

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QTabWidget,
    QCheckBox, QProgressBar, QMessageBox,
    QFileDialog, QHeaderView, QAbstractItemView,
    QListWidgetItem, QMenu, QAction, QToolBar, QStyle,
    QApplication
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor

from ..config.config_manager import ConfigManager
from ..core.mkv_editor import MKVEditor
from ..core.naming_rules import NamingRules
from ..utils.mkv_tools_checker import MKVToolsChecker
from .processing_thread import ProcessingThread
from .rules_config_widget import RulesConfigWidget


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config = ConfigManager.load_config()
        self.naming_rules = NamingRules(self.config)

        self.mkv_files = {}  # file_path -> analysis_result
        self.proposed_changes = {}  # file_path -> {title: str, tracks: {track_id: updates}}
        self.excluded_files = set()  # Set of file paths to exclude from processing
        self.processing_thread = None

        # Check for mkvtoolnix
        tools_available, tools_message = MKVToolsChecker.check_mkvtools()
        if not tools_available:
            QMessageBox.critical(
                None, "Missing dependencies",
                f"MKVToolNix is required but not found:\n{tools_message}\n\n"
                "Please install MKVToolNix:\n"
                "• Windows: Download from mkvtoolnix.download\n"
                "• macOS: brew install mkvtoolnix\n"
                "• Ubuntu/Debian: sudo apt install mkvtoolnix\n"
                "• CentOS/RHEL: sudo yum install mkvtoolnix"
            )
            sys.exit(1)

        self.init_ui()
        self.setWindowTitle("MKV Track Renamer")
        self.setGeometry(100, 100, 1400, 900)

    def init_ui(self):
        """Initialize the main UI"""
        self.create_toolbar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout()

        # Left panel - File list and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Enable drag and drop
        self.setAcceptDrops(True)

        # File controls
        file_controls = QGridLayout()
        self.add_files_btn = QPushButton("Add MKV files")
        self.add_folder_btn = QPushButton("Add folder(s)")
        self.analyze_btn = QPushButton("Analyze files")
        self.clear_files_btn = QPushButton("Clear all")

        self.add_files_btn.setToolTip("Select MKV files to add to the list")
        self.add_folder_btn.setToolTip("Select one or more folders to recursively scan for MKV files")

        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folders)
        self.clear_files_btn.clicked.connect(self.clear_files)
        self.analyze_btn.clicked.connect(self.analyze_files)

        file_controls.addWidget(self.add_files_btn, 0, 0)
        file_controls.addWidget(self.add_folder_btn, 0, 1)
        file_controls.addWidget(self.analyze_btn, 1, 0)
        file_controls.addWidget(self.clear_files_btn, 1, 1)

        # File list with context menu
        self.file_list = QListWidget()
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_file_context_menu)
        self.file_list.installEventFilter(self)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("")

        left_layout.addLayout(file_controls)
        left_layout.addWidget(QLabel("MKV files:"))
        left_layout.addWidget(self.file_list)
        left_layout.addWidget(self.progress_label)
        left_layout.addWidget(self.progress_bar)

        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(350)

        # Right panel - Tabs
        self.tab_widget = QTabWidget()

        # Rules tab
        self.rules_widget = RulesConfigWidget()
        self.tab_widget.addTab(self.rules_widget, "Naming rules")

        # Preview tab
        self.preview_widget = self.create_preview_tab()
        self.tab_widget.addTab(self.preview_widget, "Preview changes")

        # Apply tab
        self.apply_widget = self.create_apply_tab()
        self.tab_widget.addTab(self.apply_widget, "Apply changes")

        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.tab_widget, 2)

        central_widget.setLayout(main_layout)

        # Status bar
        self.statusBar().showMessage("Ready - MKVToolNix detected")

    def create_toolbar(self):
        """Create the top toolbar"""
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setObjectName("main_toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # About action
        about_action = QAction(
            self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            "About",
            self
        )
        about_action.setStatusTip("About MKV Track Renamer")
        about_action.triggered.connect(self.show_about_dialog)
        self.toolbar.addAction(about_action)

    def show_about_dialog(self):
        """Show about dialog"""
        version = QApplication.applicationVersion() or "1.2.0"
        QMessageBox.about(
            self, "MKV Track Renamer",
            f"Welcome to MKV Track Renamer v{version}!\n\n"
            "Features:\n"
            "• Edit segment titles\n"
            "• Configure default/forced track flags\n"
            "• Customizable language and codec mappings\n"
            "• Color-coded file groups in preview\n"
            "• Configuration file support\n"
            "• Resizable table columns\n"
            "• File exclusion/removal options\n"
            "• Auto-sync title to video tracks\n"
            "• Auto-update subtitle names when forced flag is toggled\n\n"
            "Getting started:\n"
            "1. Click 'Add MKV files' to select your files\n"
            "2. Click 'Analyze files' to examine track information\n"
            "3. Configure naming rules in the 'Naming rules' tab\n"
            "4. Generate and customize in the 'Preview changes' tab\n"
            "5. Apply changes in the 'Apply changes' tab\n\n"
            "Right-click files to exclude/include or remove them.\n"
            "Toggle forced flags to auto-update subtitle names.\n\n"
            "Requires: MKVToolNix (mkvpropedit, mkvmerge)"
        )

    def create_preview_tab(self) -> QWidget:
        """Create the preview changes tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Controls
        controls = QHBoxLayout()
        self.generate_names_btn = QPushButton("Generate names")
        self.generate_names_btn.clicked.connect(self.generate_names)
        controls.addWidget(self.generate_names_btn)
        controls.addStretch()

        # Preview table with enhanced columns
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(10)
        self.preview_table.setHorizontalHeaderLabels([
            "File", "Title", "Track type", "Track ID", "Current name", "Proposed name",
            "Language", "Default", "Forced", "Info"
        ])

        # Enable resizable columns
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # Allow manual resizing
        header.setStretchLastSection(True)  # Last section stretches to fill space

        # Set minimum column widths
        header.setMinimumSectionSize(60)

        # Set initial column widths
        self.preview_table.setColumnWidth(0, 150)  # File
        self.preview_table.setColumnWidth(1, 150)  # Title
        self.preview_table.setColumnWidth(2, 100)  # Track type
        self.preview_table.setColumnWidth(3, 70)   # Track ID
        self.preview_table.setColumnWidth(4, 200)  # Current name
        self.preview_table.setColumnWidth(5, 200)  # Proposed name
        self.preview_table.setColumnWidth(6, 100)  # Language
        self.preview_table.setColumnWidth(7, 80)   # Default
        self.preview_table.setColumnWidth(8, 80)   # Forced
        # Info column will stretch

        # Make editable columns
        self.preview_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.preview_table.itemChanged.connect(self.on_table_item_changed)

        layout.addLayout(controls)
        layout.addWidget(self.preview_table)

        widget.setLayout(layout)
        return widget

    def create_apply_tab(self) -> QWidget:
        """Create the apply changes tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Info
        info_label = QLabel(
            "Review the changes above and click 'Apply changes' to modify the MKV files.\n"
            "This will update segment titles, track names, and track flags as specified.\n"
            "Backup files with .bak extension will be created by default."
        )
        info_label.setWordWrap(True)

        # Controls
        controls = QHBoxLayout()
        self.apply_btn = QPushButton("Apply changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        self.apply_btn.setEnabled(False)

        self.backup_cb = QCheckBox("Create backup files")
        self.backup_cb.setChecked(False)

        controls.addWidget(self.apply_btn)
        controls.addWidget(self.backup_cb)
        controls.addStretch()

        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)

        layout.addWidget(info_label)
        layout.addLayout(controls)
        layout.addWidget(QLabel("Operation log:"))
        layout.addWidget(self.log_text)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def show_file_context_menu(self, position):
        """Show context menu for file list"""
        item = self.file_list.itemAt(position)
        if item is None:
            return

        # Find the corresponding file path
        file_path = item.data(Qt.UserRole)
        if not file_path:
            item_text = item.text()
            if item_text.startswith("[EXCLUDED] "):
                item_text = item_text[11:]
            for fp in self.mkv_files.keys():
                if Path(fp).name == item_text:
                    file_path = fp
                    break

        if file_path is None:
            return

        menu = QMenu()

        # Toggle exclude/include action
        if file_path in self.excluded_files:
            action = QAction("Include in processing", self)
            action.triggered.connect(lambda: self.include_file(file_path))
        else:
            action = QAction("Exclude from processing", self)
            action.triggered.connect(lambda: self.exclude_file(file_path))

        menu.addAction(action)

        # Remove file action
        remove_action = QAction("Remove file", self)
        remove_action.triggered.connect(lambda: self.remove_file(file_path))
        menu.addAction(remove_action)

        menu.exec_(self.file_list.mapToGlobal(position))

    def exclude_file(self, file_path: str):
        """Exclude a file from processing"""
        self.excluded_files.add(file_path)
        self.update_file_list_display()
        self.update_preview_table()
        self.statusBar().showMessage(f"Excluded {Path(file_path).name} from processing")

    def include_file(self, file_path: str):
        """Include a file back in processing"""
        self.excluded_files.discard(file_path)
        self.update_file_list_display()
        self.update_preview_table()
        self.statusBar().showMessage(f"Included {Path(file_path).name} in processing")

    def remove_file(self, file_path: str):
        """Remove a file completely"""
        # Remove from all data structures
        if file_path in self.mkv_files:
            del self.mkv_files[file_path]
        if file_path in self.proposed_changes:
            del self.proposed_changes[file_path]
        self.excluded_files.discard(file_path)

        # Update UI
        self.update_file_list_display()
        self.update_preview_table()
        self.statusBar().showMessage(f"Removed {Path(file_path).name}")

    def update_file_list_display(self):
        """Update the file list display with exclusion indicators"""
        self.file_list.clear()

        for file_path in self.mkv_files.keys():
            file_name = Path(file_path).name

            item = QListWidgetItem(file_name)
            item.setData(Qt.UserRole, file_path)
            item.setToolTip(file_path)

            # Mark excluded files visually
            if file_path in self.excluded_files:
                item.setText(f"[EXCLUDED] {file_name}")
                item.setForeground(QColor(128, 128, 128))  # Gray text

            self.file_list.addItem(item)

    def add_paths(self, paths: List[str]):
        """Add files and/or folders recursively"""
        added_count = 0
        total_found = 0
        for path_str in paths:
            if not path_str:
                continue
            p = Path(path_str)
            if not p.exists():
                continue
            if p.is_file() and p.suffix.lower() == '.mkv':
                total_found += 1
                resolved = str(p.resolve())
                if resolved not in self.mkv_files:
                    self.mkv_files[resolved] = None
                    added_count += 1
            elif p.is_dir():
                try:
                    found_in_folder = []
                    for root, dirs, files in os.walk(str(p), onerror=lambda err: None):
                        for file in files:
                            if file.lower().endswith('.mkv'):
                                found_in_folder.append(os.path.join(root, file))

                    found_in_folder.sort(key=lambda s: s.lower())
                    total_found += len(found_in_folder)

                    for file_path in found_in_folder:
                        resolved = str(Path(file_path).resolve())
                        if resolved not in self.mkv_files:
                            self.mkv_files[resolved] = None
                            added_count += 1
                except Exception as e:
                    self.log_text.append(f"Error scanning folder {p}: {str(e)}")

        self.update_file_list_display()
        if added_count > 0:
            msg = f"Added {added_count} MKV file(s)"
            self.statusBar().showMessage(msg)
            self.log_text.append(f"✓ {msg}")
        elif total_found > 0:
            msg = "All MKV files in selected location(s) already in list"
            self.statusBar().showMessage(msg)
            self.log_text.append(f"ℹ {msg}")
        else:
            msg = "No MKV files found in selected location(s)"
            self.statusBar().showMessage(msg)
            self.log_text.append(f"ℹ {msg}")

    def add_files(self):
        """Add MKV files to the list"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select MKV files", "", "MKV files (*.mkv);;All files (*.*)"
        )
        if files:
            self.add_paths(files)

    def add_folders(self):
        """Add one or more folders and recursively scan for MKV files"""
        folders = []
        dialog_succeeded = False

        if sys.platform == 'win32':
            try:
                from ..utils.native_dialog import pick_multiple_folders
                parent_hwnd = int(self.winId()) if self.winId() else 0
                folders = pick_multiple_folders(
                    parent_hwnd=parent_hwnd,
                    title="Select Folder(s) to Scan for MKV Files"
                )
                dialog_succeeded = True
            except Exception as e:
                dialog_succeeded = False
                self.log_text.append(f"Native folder dialog error ({e}), falling back to standard dialog...")

        # Fallback if non-Windows or if native dialog failed with an error
        if not dialog_succeeded:
            selected_dir = QFileDialog.getExistingDirectory(
                self, "Select Folder to Scan for MKV Files", "", QFileDialog.ShowDirsOnly
            )
            if selected_dir:
                folders = [selected_dir]

        if folders:
            self.add_paths(folders)

    def clear_files(self):
        """Clear all files from the list"""
        self.file_list.clear()
        self.mkv_files.clear()
        self.proposed_changes.clear()
        self.excluded_files.clear()
        self.preview_table.setRowCount(0)
        self.log_text.clear()
        self.apply_btn.setEnabled(False)

        self.statusBar().showMessage("Files cleared")

    def analyze_files(self):
        """Analyze all MKV files"""
        if not self.mkv_files:
            QMessageBox.warning(self, "Warning", "No files to analyze")
            return

        files_to_analyze = [f for f, data in self.mkv_files.items() if data is None]

        if not files_to_analyze:
            QMessageBox.information(self, "Info", "All files already analyzed")
            return

        # Disable controls
        self.analyze_btn.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)

        # Start processing thread
        self.processing_thread = ProcessingThread(files_to_analyze)
        self.processing_thread.progress_updated.connect(self.on_progress_updated)
        self.processing_thread.file_processed.connect(self.on_file_processed)
        self.processing_thread.finished_processing.connect(self.on_analysis_finished)
        self.processing_thread.error_occurred.connect(self.on_analysis_error)

        self.progress_bar.setMaximum(len(files_to_analyze))
        self.progress_bar.setValue(0)

        self.processing_thread.start()

    def on_progress_updated(self, current: int, message: str):
        """Handle progress update"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(message)

    def on_file_processed(self, file_path: str, result: Dict):
        """Handle file processing result"""
        self.mkv_files[file_path] = result

        if result['error']:
            self.log_text.append(f"Error analyzing {Path(file_path).name}: {result['error']}")

    def on_analysis_finished(self):
        """Handle analysis completion"""
        self.analyze_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.progress_label.setText("Analysis complete")

        analyzed_count = sum(1 for data in self.mkv_files.values() if data and not data['error'])
        error_count = sum(1 for data in self.mkv_files.values() if data and data['error'])

        self.statusBar().showMessage(
            f"Analysis complete: {analyzed_count} files analyzed, {error_count} errors"
        )

        if analyzed_count > 0:
            self.tab_widget.setCurrentIndex(1)  # Switch to preview tab

    def on_analysis_error(self, file_path: str, error: str):
        """Handle analysis error"""
        self.log_text.append(f"Error processing {Path(file_path).name}: {error}")

    def on_file_selected(self):
        """Handle file selection in the list"""
        current_item = self.file_list.currentItem()
        if not current_item:
            return

        # Find the corresponding file path
        selected_file = current_item.data(Qt.UserRole)
        if not selected_file:
            item_text = current_item.text()
            # Remove [EXCLUDED] prefix if present
            if item_text.startswith("[EXCLUDED] "):
                item_text = item_text[11:]

            for file_path in self.mkv_files.keys():
                if Path(file_path).name == item_text:
                    selected_file = file_path
                    break

        if selected_file and self.mkv_files.get(selected_file):
            self.update_preview_for_file(selected_file)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
            if paths:
                self.add_paths(paths)
                event.acceptProposedAction()

    def eventFilter(self, source, event):
        if source == self.file_list:
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.DragMove:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.Drop:
                if event.mimeData().hasUrls():
                    paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
                    if paths:
                        self.add_paths(paths)
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(source, event)

    def generate_names(self):
        """Generate proposed names and changes for all files"""
        rules = self.rules_widget.get_rules()

        # Identify existing files that already have generated names, and newly analyzed files
        existing_generated_files = [
            f for f in self.proposed_changes.keys()
            if f in self.mkv_files and self.mkv_files[f] and not self.mkv_files[f].get('error')
        ]
        new_files_to_generate = [
            f for f, data in self.mkv_files.items()
            if data and not data.get('error') and f not in self.excluded_files and f not in self.proposed_changes
        ]

        valid_files = [
            f for f, data in self.mkv_files.items()
            if data and not data.get('error') and f not in self.excluded_files
        ]

        if not valid_files:
            QMessageBox.warning(self, "Warning", "No analyzed files available to generate names for.")
            return

        # If existing generated names already exist and there are new files to add, prompt the user
        regenerate_all = True
        if existing_generated_files and new_files_to_generate:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Generate Names")
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setText(
                "A list of generated names already exists, and new analyzed files are ready to be added."
            )
            msg_box.setInformativeText(
                "How would you like to proceed?\n\n"
                "• Add new files only: Adds only the new files to the names list, "
                "keeping any manual edits to existing names intact.\n"
                "• Regenerate all: Regenerates the complete list of names "
                "(any manual edits performed beforehand will be lost).\n"
                "• Cancel: Cancels the operation without making changes."
            )

            add_new_btn = msg_box.addButton("Add new files only", QMessageBox.AcceptRole)
            regen_btn = msg_box.addButton("Regenerate all", QMessageBox.DestructiveRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)

            msg_box.setDefaultButton(add_new_btn)
            msg_box.exec_()

            clicked = msg_box.clickedButton()
            if clicked == cancel_btn:
                return
            elif clicked == add_new_btn:
                regenerate_all = False
            else:
                regenerate_all = True

        if regenerate_all:
            self.proposed_changes.clear()
            files_to_process = [
                (f, self.mkv_files[f]) for f in valid_files
            ]
        else:
            files_to_process = [
                (f, self.mkv_files[f]) for f in new_files_to_generate
            ]

        for file_path, data in files_to_process:
            # Initialize file changes
            file_changes = {
                'title': data.get('title', ''),
                'tracks': {}
            }

            # Generate track names and preserve current flags
            for track in data['tracks']:
                if track['track_type'] == 'video':
                    # Handle video track naming based on rules
                    if rules.get('video', {}).get('copy_title_to_video', True):
                        # Use file title for video tracks (default behavior)
                        proposed_name = file_changes['title']
                    else:
                        # Generate name based on format (previous behavior)
                        proposed_name = self.naming_rules.generate_track_name(track, rules)
                else:
                    # For non-video tracks, use normal generation
                    proposed_name = self.naming_rules.generate_track_name(track, rules)

                file_changes['tracks'][track['track_id']] = {
                    'name': proposed_name,
                    'language': track.get('language', 'und'),
                    'default': track.get('default', False),
                    'forced': track.get('forced', False)
                }

            self.proposed_changes[file_path] = file_changes

        self.update_preview_table()
        self.apply_btn.setEnabled(True)

        if not regenerate_all:
            self.statusBar().showMessage(
                f"Added {len(files_to_process)} new file(s) to names list (existing changes kept)"
            )
        else:
            self.statusBar().showMessage("Names and changes generated")

    def update_preview_for_file(self, file_path: str):
        """Update preview table for a specific file"""
        data = self.mkv_files.get(file_path)
        if not data or data['error']:
            return

        # This would be used for single file preview
        # For now, we'll update the entire table
        self.update_preview_table()

    def get_alternating_colors(self, file_index: int) -> Tuple[QColor, QColor]:
        """Get alternating background colors for file groups"""
        colors = [
            (QColor(255, 255, 255), QColor(240, 240, 240)),  # White/Light Gray
            (QColor(250, 250, 255), QColor(235, 235, 255)),  # Light Blue
            (QColor(250, 255, 250), QColor(235, 255, 235)),  # Light Green
            (QColor(255, 250, 250), QColor(255, 235, 235)),  # Light Pink
            (QColor(255, 255, 250), QColor(255, 255, 235)),  # Light Yellow
        ]
        return colors[file_index % len(colors)]

    def update_preview_table(self):
        """Update the preview table with all files and tracks"""
        self.preview_table.blockSignals(True)
        self.preview_table.setRowCount(0)

        row = 0
        file_index = 0

        for file_path, data in self.mkv_files.items():
            if not data or data['error'] or file_path in self.excluded_files:
                continue

            file_name = Path(file_path).name
            file_changes = self.proposed_changes.get(file_path, {'title': '', 'tracks': {}})

            # Get colors for this file group
            bg_color, alt_bg_color = self.get_alternating_colors(file_index)

            # Add title row
            self.preview_table.insertRow(row)

            # File name
            file_item = QTableWidgetItem(file_name)
            file_item.setBackground(bg_color)
            self.preview_table.setItem(row, 0, file_item)

            # Title (editable)
            title_item = QTableWidgetItem(file_changes['title'])
            title_item.setData(Qt.UserRole, ('title', file_path, None))
            title_item.setBackground(bg_color)
            self.preview_table.setItem(row, 1, title_item)

            # Fill other columns for title row
            for col in range(2, 10):
                empty_item = QTableWidgetItem("")
                empty_item.setBackground(bg_color)
                if col == 2:
                    empty_item.setText("TITLE")
                    empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
                else:
                    empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, col, empty_item)

            row += 1

            # Add track rows
            track_row_alt = False
            for track in data['tracks']:
                self.preview_table.insertRow(row)

                # Choose background color (alternating within file group)
                current_bg = alt_bg_color if track_row_alt else bg_color
                track_row_alt = not track_row_alt

                track_changes = file_changes['tracks'].get(track['track_id'], {})

                # File name (empty for track rows)
                file_item = QTableWidgetItem("")
                file_item.setBackground(current_bg)
                file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, 0, file_item)

                # Title (empty for track rows)
                title_item = QTableWidgetItem("")
                title_item.setBackground(current_bg)
                title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, 1, title_item)

                # Track type
                type_item = QTableWidgetItem(track['track_type'].title())
                type_item.setBackground(current_bg)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, 2, type_item)

                # Track ID
                id_item = QTableWidgetItem(str(track.get('track_id', '')))
                id_item.setTextAlignment(Qt.AlignCenter)
                id_item.setBackground(current_bg)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, 3, id_item)

                # Current name
                current_name = track.get('name', '') or f"Track {track['track_id'] + 1}"
                current_item = QTableWidgetItem(current_name)
                current_item.setBackground(current_bg)
                current_item.setFlags(current_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, 4, current_item)

                # Proposed name (editable)
                proposed_name = track_changes.get('name', '')
                proposed_item = QTableWidgetItem(proposed_name)
                proposed_item.setData(Qt.UserRole, ('track_name', file_path, track['track_id']))
                proposed_item.setBackground(current_bg)
                self.preview_table.setItem(row, 5, proposed_item)

                # Language (editable)
                language = track_changes.get('language', track.get('language', 'und'))
                lang_item = QTableWidgetItem(language)
                lang_item.setData(Qt.UserRole, ('track_language', file_path, track['track_id']))
                lang_item.setBackground(current_bg)
                self.preview_table.setItem(row, 6, lang_item)

                # Default checkbox
                default_cb = QCheckBox()
                default_cb.setChecked(track_changes.get('default', track.get('default', False)))
                default_cb.stateChanged.connect(
                    lambda state, fp=file_path, tid=track['track_id']:
                    self.on_checkbox_changed('default', fp, tid, state == Qt.Checked)
                )
                default_widget = QWidget()
                default_layout = QHBoxLayout()
                default_layout.addWidget(default_cb)
                default_layout.setAlignment(Qt.AlignCenter)
                default_layout.setContentsMargins(0, 0, 0, 0)
                default_widget.setLayout(default_layout)
                self.preview_table.setCellWidget(row, 7, default_widget)

                # Forced checkbox
                forced_cb = QCheckBox()
                forced_cb.setChecked(track_changes.get('forced', track.get('forced', False)))
                forced_cb.stateChanged.connect(
                    lambda state, fp=file_path, tid=track['track_id']:
                    self.on_checkbox_changed('forced', fp, tid, state == Qt.Checked)
                )
                forced_widget = QWidget()
                forced_layout = QHBoxLayout()
                forced_layout.addWidget(forced_cb)
                forced_layout.setAlignment(Qt.AlignCenter)
                forced_layout.setContentsMargins(0, 0, 0, 0)
                forced_widget.setLayout(forced_layout)
                self.preview_table.setCellWidget(row, 8, forced_widget)

                # Additional info
                info_parts = []
                if track['track_type'] == 'video':
                    if track.get('width') and track.get('height'):
                        info_parts.append(f"{track['width']}x{track['height']}")
                elif track['track_type'] == 'audio':
                    if track.get('channels'):
                        info_parts.append(f"{track['channels']}ch")
                    if track.get('sample_rate'):
                        info_parts.append(f"{int(track['sample_rate'] / 1000)}kHz")

                info_parts.append(track.get('codec', ''))
                info = ', '.join(filter(None, info_parts))
                info_item = QTableWidgetItem(info)
                info_item.setBackground(current_bg)
                info_item.setFlags(info_item.flags() & ~Qt.ItemIsEditable)
                self.preview_table.setItem(row, 9, info_item)

                row += 1

            file_index += 1

        self.preview_table.blockSignals(False)

    def on_table_item_changed(self, item: QTableWidgetItem):
        """Handle changes in table items"""
        data = item.data(Qt.UserRole)
        if not data:
            return

        change_type, file_path, track_id = data
        new_value = item.text()

        if file_path not in self.proposed_changes:
            return

        if change_type == 'title':
            self.proposed_changes[file_path]['title'] = new_value
            # Update video track names to match title
            self.sync_title_to_video_tracks(file_path, new_value)
        elif change_type == 'track_name':
            if track_id in self.proposed_changes[file_path]['tracks']:
                self.proposed_changes[file_path]['tracks'][track_id]['name'] = new_value
        elif change_type == 'track_language':
            if track_id in self.proposed_changes[file_path]['tracks']:
                self.proposed_changes[file_path]['tracks'][track_id]['language'] = new_value

    def sync_title_to_video_tracks(self, file_path: str, title: str):
        """Sync title changes to video track names and update the table"""
        if file_path not in self.mkv_files or file_path not in self.proposed_changes:
            return

        data = self.mkv_files[file_path]
        if not data or data['error']:
            return

        # Check if we should copy title to video tracks based on current rules
        rules = self.rules_widget.get_rules()
        if not rules.get('video', {}).get('copy_title_to_video', True):
            return  # Don't sync if the option is disabled

        # Find video tracks and update their names
        for track in data['tracks']:
            if track['track_type'] == 'video':
                track_id = track['track_id']
                if track_id in self.proposed_changes[file_path]['tracks']:
                    self.proposed_changes[file_path]['tracks'][track_id]['name'] = title

        # Update the table display
        self.update_video_track_names_in_table(file_path, title)

    def update_video_track_names_in_table(self, file_path: str, title: str):
        """Update video track name fields in the table"""
        # Check if we should update video track names based on current rules
        rules = self.rules_widget.get_rules()
        if not rules.get('video', {}).get('copy_title_to_video', True):
            return  # Don't update if the option is disabled

        for row in range(self.preview_table.rowCount()):
            # Check if this row contains a video track name for the specific file
            proposed_name_item = self.preview_table.item(row, 5)  # Proposed name column
            if proposed_name_item:
                data = proposed_name_item.data(Qt.UserRole)
                if data:
                    change_type, item_file_path, track_id = data
                    if (change_type == 'track_name' and
                            item_file_path == file_path and
                            track_id is not None):

                        # Check if this is a video track
                        track_type_item = self.preview_table.item(row, 2)
                        if track_type_item and track_type_item.text().lower() == 'video':
                            # Update the proposed name
                            proposed_name_item.setText(title)

    def on_checkbox_changed(self, flag_type: str, file_path: str, track_id: int, checked: bool):
        """Handle checkbox state changes"""
        if file_path not in self.proposed_changes:
            return

        if track_id in self.proposed_changes[file_path]['tracks']:
            self.proposed_changes[file_path]['tracks'][track_id][flag_type] = checked

            # If this is a forced flag change on a subtitle track, update the track name
            if flag_type == 'forced':
                self.update_forced_flag_in_name(file_path, track_id, checked)

    def update_forced_flag_in_name(self, file_path: str, track_id: int, forced: bool):
        """Update track name when forced flag changes for subtitle tracks"""
        if file_path not in self.mkv_files or file_path not in self.proposed_changes:
            return

        data = self.mkv_files[file_path]
        if not data or data['error']:
            return

        # Find the track
        track_info = None
        for track in data['tracks']:
            if track['track_id'] == track_id:
                track_info = track
                break

        if not track_info or track_info['track_type'] != 'subtitles':
            return  # Only update subtitle tracks

        # Get current rules
        rules = self.rules_widget.get_rules()

        # Get current proposed name
        current_name = self.proposed_changes[file_path]['tracks'][track_id]['name']

        # Update name based on forced flag
        new_name = self.naming_rules.update_subtitle_forced_flag(
            current_name, forced, track_info, rules
        )

        # Update the proposed changes
        self.proposed_changes[file_path]['tracks'][track_id]['name'] = new_name

        # Update the table display
        self.update_track_name_in_table(file_path, track_id, new_name)

    def update_track_name_in_table(self, file_path: str, track_id: int, new_name: str):
        """Update a specific track name in the preview table"""
        for row in range(self.preview_table.rowCount()):
            proposed_name_item = self.preview_table.item(row, 5)  # Proposed name column
            if proposed_name_item:
                data = proposed_name_item.data(Qt.UserRole)
                if data:
                    change_type, item_file_path, item_track_id = data
                    if (change_type == 'track_name' and
                            item_file_path == file_path and
                            item_track_id == track_id):
                        # Update the table item
                        proposed_name_item.setText(new_name)
                        break

    def apply_changes(self):
        """Apply all proposed changes to MKV files"""
        if not self.proposed_changes:
            QMessageBox.warning(self, "Warning", "No changes to apply")
            return

        # Filter out excluded files
        changes_to_apply = {fp: changes for fp, changes in self.proposed_changes.items()
                            if fp not in self.excluded_files}

        if not changes_to_apply:
            QMessageBox.warning(self, "Warning", "No files selected for processing")
            return

        reply = QMessageBox.question(
            self, "Confirm changes",
            f"This will modify {len(changes_to_apply)} MKV files with all proposed changes "
            "(titles, track names, languages, and flags). Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.apply_btn.setEnabled(False)
        self.log_text.clear()

        success_count = 0
        error_count = 0

        for file_path, changes in changes_to_apply.items():
            try:
                self.log_text.append(f"Processing: {Path(file_path).name}")

                # Prepare segment title
                segment_title = changes.get('title', '').strip()

                # Prepare track updates
                track_updates = {}
                for track_id, track_changes in changes.get('tracks', {}).items():
                    updates = {}

                    # Track name
                    if track_changes.get('name', '').strip():
                        updates['name'] = track_changes['name'].strip()

                    # Language
                    if track_changes.get('language', '').strip():
                        updates['language'] = track_changes['language'].strip()

                    # Flags
                    updates['default'] = track_changes.get('default', False)
                    updates['forced'] = track_changes.get('forced', False)

                    track_updates[track_id] = updates

                # Apply changes using mkvpropedit
                success, message = MKVEditor.update_mkv_properties(
                    file_path, segment_title, track_updates, self.backup_cb.isChecked()
                )

                if success:
                    if segment_title:
                        self.log_text.append(f"  Title: '{segment_title}'")

                    for track_id, updates in track_updates.items():
                        changes_list = []
                        if 'name' in updates:
                            changes_list.append(f"name='{updates['name']}'")
                        if 'language' in updates:
                            changes_list.append(f"lang={updates['language']}")
                        if updates.get('default'):
                            changes_list.append("default=yes")
                        if updates.get('forced'):
                            changes_list.append("forced=yes")

                        if changes_list:
                            self.log_text.append(f"  Track {track_id + 1}: {', '.join(changes_list)}")

                    self.log_text.append(f"  ✓ {message}")
                    success_count += 1
                else:
                    self.log_text.append(f"  ✗ {message}")
                    error_count += 1

            except Exception as e:
                self.log_text.append(f"  ✗ Unexpected error: {str(e)}")
                error_count += 1

        self.apply_btn.setEnabled(True)

        # Show completion message
        if success_count > 0 or error_count > 0:
            QMessageBox.information(
                self, "Operation complete",
                f"Processing complete:\n"
                f"Successfully updated: {success_count} files\n"
                f"Errors: {error_count} files\n\n"
                f"Check the log for details."
            )

        self.statusBar().showMessage(f"Applied changes: {success_count} success, {error_count} errors")
