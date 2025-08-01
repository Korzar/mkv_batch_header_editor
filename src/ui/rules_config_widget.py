"""
Rules configuration widget for track naming
"""

from typing import Dict

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QCheckBox


class RulesConfigWidget(QWidget):
    """Widget for configuring naming rules"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_default_rules()

    def init_ui(self):
        """Initialize the rules configuration UI"""
        layout = QVBoxLayout()

        # Video rules
        video_group = QGroupBox("Video track rules")
        video_layout = QVBoxLayout()

        self.video_codec_cb = QCheckBox("Include codec")
        self.video_resolution_cb = QCheckBox("Include resolution")
        self.video_fps_cb = QCheckBox("Include frame rate")
        self.video_copy_title_cb = QCheckBox("Copy file title to video track")

        video_layout.addWidget(self.video_copy_title_cb)
        video_layout.addWidget(self.video_codec_cb)
        video_layout.addWidget(self.video_resolution_cb)
        video_layout.addWidget(self.video_fps_cb)
        video_group.setLayout(video_layout)

        # Audio rules
        audio_group = QGroupBox("Audio track rules")
        audio_layout = QVBoxLayout()

        self.audio_language_cb = QCheckBox("Include language")
        self.audio_codec_cb = QCheckBox("Include codec")
        self.audio_channels_cb = QCheckBox("Include channel configuration")
        self.audio_sample_rate_cb = QCheckBox("Include sample rate")

        audio_layout.addWidget(self.audio_language_cb)
        audio_layout.addWidget(self.audio_codec_cb)
        audio_layout.addWidget(self.audio_channels_cb)
        audio_layout.addWidget(self.audio_sample_rate_cb)
        audio_group.setLayout(audio_layout)

        # Subtitle rules
        subtitle_group = QGroupBox("Subtitle track rules")
        subtitle_layout = QVBoxLayout()

        self.subtitle_language_cb = QCheckBox("Include language")
        self.subtitle_format_cb = QCheckBox("Include format")
        self.subtitle_flags_cb = QCheckBox("Include forced/default flags")

        subtitle_layout.addWidget(self.subtitle_language_cb)
        subtitle_layout.addWidget(self.subtitle_format_cb)
        subtitle_layout.addWidget(self.subtitle_flags_cb)
        subtitle_group.setLayout(subtitle_layout)

        layout.addWidget(video_group)
        layout.addWidget(audio_group)
        layout.addWidget(subtitle_group)
        layout.addStretch()

        self.setLayout(layout)

    def load_default_rules(self):
        """Load default naming rules"""
        # Video defaults
        self.video_copy_title_cb.setChecked(True)
        self.video_codec_cb.setChecked(True)
        self.video_resolution_cb.setChecked(True)
        self.video_fps_cb.setChecked(False)

        # Audio defaults
        self.audio_language_cb.setChecked(True)
        self.audio_codec_cb.setChecked(True)
        self.audio_channels_cb.setChecked(True)
        self.audio_sample_rate_cb.setChecked(False)

        # Subtitle defaults
        self.subtitle_language_cb.setChecked(True)
        self.subtitle_format_cb.setChecked(True)
        self.subtitle_flags_cb.setChecked(True)

    def get_rules(self) -> Dict:
        """Get current naming rules"""
        return {
            'video': {
                'copy_title_to_video': self.video_copy_title_cb.isChecked(),
                'include_codec': self.video_codec_cb.isChecked(),
                'include_resolution': self.video_resolution_cb.isChecked(),
                'include_fps': self.video_fps_cb.isChecked()
            },
            'audio': {
                'include_language': self.audio_language_cb.isChecked(),
                'include_codec': self.audio_codec_cb.isChecked(),
                'include_channels': self.audio_channels_cb.isChecked(),
                'include_sample_rate': self.audio_sample_rate_cb.isChecked()
            },
            'subtitles': {
                'include_language': self.subtitle_language_cb.isChecked(),
                'include_format': self.subtitle_format_cb.isChecked(),
                'include_flags': self.subtitle_flags_cb.isChecked()
            }
        }
