#!/usr/bin/env python3
"""
MKV Track Renamer - A PyQt application for batch renaming MKV track headers
"""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from src.ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("MKV Track Renamer")
    app.setApplicationVersion("1.2.0")
    app.setOrganizationName("NotOnlyDev")

    # Create and show main window
    try:
        window = MainWindow()
        window.show()

        # Show welcome message
        QTimer.singleShot(100, lambda: QMessageBox.about(
            window, "MKV Track Renamer",
            "Welcome to MKV Track Renamer v1.2.0!\n\n"
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
        ))

        sys.exit(app.exec_())

    except Exception as e:
        QMessageBox.critical(
            None, "Application error",
            f"Failed to start application:\n{str(e)}\n\n"
            f"Make sure MKVToolNix is installed and available in PATH."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
