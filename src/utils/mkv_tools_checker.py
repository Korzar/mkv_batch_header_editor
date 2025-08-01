"""
MKV tools availability checker
"""

import shutil
from typing import Tuple


class MKVToolsChecker:
    """Check for mkvtoolnix availability"""

    @staticmethod
    def check_mkvtools() -> Tuple[bool, str]:
        """Check if mkvpropedit and mkvmerge are available"""
        tools = ['mkvpropedit', 'mkvmerge']
        missing = []

        for tool in tools:
            if not shutil.which(tool):
                missing.append(tool)

        if missing:
            return False, f"Missing tools: {', '.join(missing)}"

        return True, "All tools available"
