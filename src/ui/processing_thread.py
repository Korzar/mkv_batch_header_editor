"""
Background processing thread for MKV file analysis
"""

from pathlib import Path
from typing import List

from PyQt5.QtCore import QThread, pyqtSignal

from ..core.mkv_analyzer import MKVAnalyzer


class ProcessingThread(QThread):
    """Thread for processing MKV files"""

    progress_updated = pyqtSignal(int, str)
    file_processed = pyqtSignal(str, dict)
    finished_processing = pyqtSignal()
    error_occurred = pyqtSignal(str, str)

    def __init__(self, files: List[str]):
        super().__init__()
        self.files = files
        self.should_stop = False

    def run(self):
        """Process files in separate thread"""
        for i, file_path in enumerate(self.files):
            if self.should_stop:
                break

            self.progress_updated.emit(i + 1, f"Analyzing: {Path(file_path).name}")

            try:
                result = MKVAnalyzer.analyze_file(file_path)
                self.file_processed.emit(file_path, result)
            except Exception as e:
                self.error_occurred.emit(file_path, str(e))

        self.finished_processing.emit()

    def stop(self):
        """Stop processing"""
        self.should_stop = True
