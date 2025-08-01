"""
MKV file editing functionality
"""

import os
import shutil
import subprocess
from typing import Dict, Tuple


class MKVEditor:
    """Handles MKV file editing using mkvpropedit"""

    @staticmethod
    def update_mkv_properties(file_path: str, segment_title: str, track_updates: Dict, create_backup: bool = True) -> \
            Tuple[bool, str]:
        """Update segment title and track properties in MKV file using mkvpropedit"""
        try:
            # Create backup if requested
            if create_backup:
                backup_path = file_path + '.bak'
                if not os.path.exists(backup_path):
                    shutil.copy2(file_path, backup_path)

            # Build mkvpropedit command
            cmd = ['mkvpropedit', file_path]

            # Set segment title if provided
            if segment_title.strip():
                cmd.extend(['--edit', 'info', '--set', f'title={segment_title}'])

            # Update track properties
            for track_id, updates in track_updates.items():
                track_num = track_id + 1  # mkvpropedit uses 1-based indexing

                # Update track name
                if 'name' in updates and updates['name'].strip():
                    cmd.extend(['--edit', f'track:{track_num}', '--set', f'name={updates["name"]}'])

                # Update default flag
                if 'default' in updates:
                    flag_value = '1' if updates['default'] else '0'
                    cmd.extend(['--edit', f'track:{track_num}', '--set', f'flag-default={flag_value}'])

                # Update forced flag
                if 'forced' in updates:
                    flag_value = '1' if updates['forced'] else '0'
                    cmd.extend(['--edit', f'track:{track_num}', '--set', f'flag-forced={flag_value}'])

                # Update language
                if 'language' in updates and updates['language'].strip():
                    cmd.extend(['--edit', f'track:{track_num}', '--set', f'language={updates["language"]}'])

            # Execute the command only if there are changes
            if len(cmd) > 2:  # More than just ['mkvpropedit', file_path]
                result = subprocess.run(cmd, capture_output=True, text=True,
                                        encoding='utf-8', errors='replace', check=True)
                return True, "Successfully updated MKV properties"
            else:
                return True, "No changes to apply"

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            # Try to decode error message properly
            try:
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
            except:
                pass
            return False, f"mkvpropedit error: {error_msg}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
