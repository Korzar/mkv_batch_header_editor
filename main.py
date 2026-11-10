#!/usr/bin/env python3
"""
MKV Track Renamer - A PyQt application for batch renaming MKV track headers
"""

import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

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
