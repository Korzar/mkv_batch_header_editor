"""
Track naming rules and generation
"""

import re
from typing import Dict


class NamingRules:
    """Handles track naming rule generation with configuration support"""

    def __init__(self, config: Dict):
        self.config = config

    def generate_track_name(self, track_info: Dict, rules: Dict) -> str:
        """Generate track name based on rules and track information"""
        track_type = track_info['track_type']

        if track_type == 'video':
            return self._generate_video_name(track_info, rules.get('video', {}))
        elif track_type == 'audio':
            return self._generate_audio_name(track_info, rules.get('audio', {}))
        elif track_type == 'subtitles':
            return self._generate_subtitle_name(track_info, rules.get('subtitles', {}))
        else:
            return f"{track_type.title()} Track"

    def _generate_video_name(self, track_info: Dict, rules: Dict) -> str:
        """Generate video track name"""
        # Check if we should copy file title to video track (default behavior)
        if rules.get('copy_title_to_video', True):
            # This will be handled by the calling function that has access to file title
            # Return empty string to indicate title should be used
            return ""

        # Generate name based on format (previous behavior)
        parts = []

        if rules.get('include_codec', True):
            codec = track_info.get('codec', '')
            # Use config mapping or fallback to codec cleanup
            display_codec = self.config.get('video_codecs', {}).get(codec)
            if not display_codec:
                # Fallback codec name cleanup
                if 'H264' in codec.upper() or 'AVC' in codec.upper():
                    display_codec = 'H.264'
                elif 'H265' in codec.upper() or 'HEVC' in codec.upper():
                    display_codec = 'H.265'
                elif 'VP9' in codec.upper():
                    display_codec = 'VP9'
                elif 'VP8' in codec.upper():
                    display_codec = 'VP8'
                elif 'AV1' in codec.upper():
                    display_codec = 'AV1'
                else:
                    display_codec = codec.replace('V_', '').replace('/', '_')
            parts.append(display_codec)

        if rules.get('include_resolution', True):
            width = track_info.get('width', 0)
            height = track_info.get('height', 0)
            if width and height:
                # Common resolution names
                if width == 1920 and height == 1080:
                    parts.append('1080p')
                elif width == 1280 and height == 720:
                    parts.append('720p')
                elif width == 3840 and height == 2160:
                    parts.append('4K')
                elif width == 2560 and height == 1440:
                    parts.append('1440p')
                else:
                    parts.append(f"{width}x{height}")

        if rules.get('include_fps', False):
            fps = track_info.get('fps', 0)
            if fps:
                # Convert from nanoseconds to fps if needed
                if fps > 1000000:  # Likely in nanoseconds
                    fps = 1000000000 / fps
                parts.append(f"{fps:.0f}fps")

        return ' '.join(parts) or 'Video'

    def _generate_audio_name(self, track_info: Dict, rules: Dict) -> str:
        """Generate audio track name"""
        parts = []

        # Language
        if rules.get('include_language', True):
            lang = track_info.get('language', 'und')
            # if lang != 'und':
            display_lang = self.config.get('languages', {}).get(lang, lang.upper())
            parts.append(display_lang)

        # Codec
        if rules.get('include_codec', True):
            codec = track_info.get('codec', '')
            # Use config mapping or fallback to codec cleanup
            display_codec = self.config.get('audio_codecs', {}).get(codec)
            if not display_codec:
                # Fallback codec name cleanup
                codec_upper = codec.upper()
                if 'DTS' in codec_upper:
                    if 'DTS-HD' in codec_upper:
                        display_codec = 'DTS-HD'
                    elif 'DTS-X' in codec_upper:
                        display_codec = 'DTS-X'
                    else:
                        display_codec = 'DTS'
                elif 'AC3' in codec_upper or 'AC-3' in codec_upper:
                    display_codec = 'AC3'
                elif 'EAC3' in codec_upper or 'E-AC-3' in codec_upper:
                    if 'JOC' in codec_upper:
                        display_codec = 'E-AC-3 JOC'
                    else:
                        display_codec = 'E-AC-3'
                elif 'AAC' in codec_upper:
                    display_codec = 'AAC'
                elif 'FLAC' in codec_upper:
                    display_codec = 'FLAC'
                elif 'VORBIS' in codec_upper:
                    display_codec = 'Vorbis'
                elif 'OPUS' in codec_upper:
                    display_codec = 'Opus'
                elif 'MP3' in codec_upper:
                    display_codec = 'MP3'
                else:
                    display_codec = codec.replace('A_', '').replace('/', '_')
            parts.append(display_codec)

        # Channels
        if rules.get('include_channels', True):
            channels = track_info.get('channels', 0)
            if channels:
                if channels == 1:
                    parts.append('1.0')
                elif channels == 2:
                    parts.append('2.0')
                elif channels == 6:
                    parts.append('5.1')
                elif channels == 8:
                    parts.append('7.1')
                else:
                    parts.append(f"{channels}ch")

        # Sample rate
        if rules.get('include_sample_rate', False):
            sample_rate = track_info.get('sample_rate', 0)
            if sample_rate:
                parts.append(f"{int(sample_rate / 1000)}kHz")

        return ' '.join(parts) or 'Audio'

    def _generate_subtitle_name(self, track_info: Dict, rules: Dict) -> str:
        """Generate subtitle track name"""
        parts = []

        # Language
        if rules.get('include_language', True):
            lang = track_info.get('language', 'und')
            if lang != 'und':
                display_lang = self.config.get('languages', {}).get(lang, lang.upper())
                parts.append(display_lang)

        # Forced/Default indicators
        if rules.get('include_flags', True):
            if track_info.get('forced', False):
                parts.append('(forzados)')
            # if track_info.get('default', False):
            #     parts.append('')

        # Format
        if rules.get('include_format', True):
            codec = track_info.get('codec', '')
            # Use config mapping or fallback to codec cleanup
            display_codec = self.config.get('subtitle_codecs', {}).get(codec)
            if not display_codec:
                # Fallback codec name cleanup
                codec_upper = codec.upper()
                if 'SUBRIP' in codec_upper or 'SRT' in codec_upper:
                    display_codec = 'SRT'
                elif 'ASS' in codec_upper or 'SSA' in codec_upper:
                    display_codec = 'ASS'
                elif 'PGS' in codec_upper:
                    display_codec = 'PGS'
                elif 'VOBSUB' in codec_upper:
                    display_codec = 'VobSub'
                elif 'WEBVTT' in codec_upper:
                    display_codec = 'WebVTT'
                else:
                    display_codec = codec.replace('S_', '').replace('/', '_')
            parts.append(display_codec)

        return ' '.join(parts) or 'Subtitles'

    def update_subtitle_forced_flag(self, current_name: str, forced: bool, track_info: Dict, rules: Dict) -> str:
        """Update subtitle track name by adding/removing (forzados) flag"""
        if track_info.get('track_type') != 'subtitles':
            return current_name

        # If flags are not included in rules, don't modify the name 
        if not rules.get('subtitles', {}).get('include_flags', True):
            return current_name

        # Remove existing (forzados) if present
        name_without_forced = re.sub(r'\s*\(forzados\)\s*', ' ', current_name).strip()
        name_without_forced = re.sub(r'\s+', ' ', name_without_forced)  # Clean up multiple spaces

        if not forced:
            # If not forced, return name without (forzados)
            return name_without_forced

        # If forced, we need to add (forzados) in the right position
        # Parse the current name to find where to insert (forzados)
        parts = name_without_forced.split()

        # Get language and format info
        lang = track_info.get('language', 'und')
        display_lang = self.config.get('languages', {}).get(lang, lang.upper()) if lang != 'und' else None

        # Get format
        codec = track_info.get('codec', '')
        display_codec = self.config.get('subtitle_codecs', {}).get(codec)
        if not display_codec:
            # Fallback codec name cleanup
            codec_upper = codec.upper()
            if 'SUBRIP' in codec_upper or 'SRT' in codec_upper:
                display_codec = '[SRT]'
            elif 'ASS' in codec_upper or 'SSA' in codec_upper:
                display_codec = '[ASS]'
            elif 'PGS' in codec_upper:
                display_codec = '[PGS]'
            elif 'VOBSUB' in codec_upper:
                display_codec = '[VOB]'
            elif 'WEBVTT' in codec_upper:
                display_codec = '[VTT]'
            else:
                display_codec = f"[{codec.replace('S_', '').replace('/', '_')}]"

        # Rebuild name with (forzados) in correct position
        new_parts = []

        # Add language if present and should be included
        if rules.get('subtitles', {}).get('include_language', True) and display_lang:
            new_parts.append(display_lang)

        # Add (forzados) flag
        new_parts.append('(forzados)')

        # Add format if should be included
        if rules.get('subtitles', {}).get('include_format', True):
            new_parts.append(display_codec)

        return ' '.join(new_parts) or 'Subtitles'
