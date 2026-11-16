"""
MKV file analysis functionality
"""

import json
import sys
import subprocess
from typing import Dict


class MKVAnalyzer:
    """Handles MKV file analysis using mkvmerge"""

    @staticmethod
    def analyze_file(file_path: str) -> Dict:
        """Analyze MKV file and extract track information using mkvmerge"""
        try:
            extra_kwargs = {}
            if sys.platform == 'win32':
                extra_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            # Use mkvmerge to get JSON info about the file with UTF-8 encoding
            cmd = ['mkvmerge', '-J', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                                    errors='replace', check=True, **extra_kwargs)

            data = json.loads(result.stdout)
            tracks = []

            # Extract track information
            for track in data.get('tracks', []):
                track_info = {
                    'index': len(tracks),
                    'track_id': track.get('id', 0),
                    'track_type': track.get('type', 'unknown'),
                    'codec': track.get('codec', 'Unknown'),
                    'language': track.get('properties', {}).get('language', 'und'),
                    'name': track.get('properties', {}).get('track_name', ''),
                    'default': track.get('properties', {}).get('default_track', False),
                    'forced': track.get('properties', {}).get('forced_track', False)
                }

                # Enhanced codec detection for E-AC-3 JOC (Dolby Atmos)
                if track_info['track_type'] == 'audio':
                    codec_id = track.get('codec_id', '')
                    codec_private = track.get('codec_private_data', '')

                    # Check for E-AC-3 JOC (Dolby Atmos hybrid)
                    if ('E-AC-3' in track_info['codec'] or 'EAC3' in codec_id.upper()):
                        # Check for JOC (Joint Object Coding) indicators
                        # This can be detected through codec private data or track properties
                        if ('JOC' in str(codec_private).upper() or
                                'ATMOS' in track_info['name'].upper() or
                                track.get('properties', {}).get('codec_private_length', 0) > 10):
                            # Additional check: E-AC-3 JOC typically has specific private data patterns
                            track_info['codec'] = 'E-AC-3 JOC'

                # Ensure proper UTF-8 handling for track name
                if track_info['name']:
                    try:
                        # If the name contains weird characters, try to fix encoding issues
                        track_info['name'] = track_info['name'].encode('latin1').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        # If that fails, keep the original name
                        pass

                # Add type-specific information
                props = track.get('properties', {})
                if track_info['track_type'] == 'video':
                    track_info.update({
                        'width': props.get('pixel_dimensions', '0x0').split('x')[
                            0] if 'pixel_dimensions' in props else 0,
                        'height': props.get('pixel_dimensions', '0x0').split('x')[
                            1] if 'pixel_dimensions' in props else 0,
                        'fps': props.get('default_duration', 0)
                    })
                    # Convert width/height to int
                    try:
                        track_info['width'] = int(track_info['width'])
                        track_info['height'] = int(track_info['height'])
                    except (ValueError, TypeError):
                        track_info['width'] = 0
                        track_info['height'] = 0

                elif track_info['track_type'] == 'audio':
                    track_info.update({
                        'channels': props.get('audio_channels', 0),
                        'sample_rate': props.get('audio_sampling_frequency', 0),
                        'bit_depth': props.get('audio_bits_per_sample', 0)
                    })
                elif track_info['track_type'] == 'subtitles':
                    track_info.update({
                        'format': track_info['codec']
                    })

                tracks.append(track_info)

            # Get container info with proper UTF-8 handling
            container = data.get('container', {})
            title = container.get('properties', {}).get('title', '')

            # Fix encoding issues for title if needed
            if title:
                try:
                    title = title.encode('latin1').decode('utf-8')
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass

            return {
                'file_path': file_path,
                'tracks': tracks,
                'title': title,
                'error': None
            }

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            # Try to decode error message properly
            try:
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
            except:
                pass
            return {
                'file_path': file_path,
                'tracks': [],
                'title': '',
                'error': f"mkvmerge error: {error_msg}"
            }
        except json.JSONDecodeError as e:
            return {
                'file_path': file_path,
                'tracks': [],
                'title': '',
                'error': f"JSON parsing error: {str(e)}"
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'tracks': [],
                'title': '',
                'error': f"Unexpected error: {str(e)}"
            }
