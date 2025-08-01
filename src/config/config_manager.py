"""
Configuration management for MKV Track Renamer
"""

from typing import Dict


class ConfigManager:
    """Manages application configuration"""

    DEFAULT_CONFIG = {
        "languages": {
            "und": "Desconocido",
            "eng": "Inglés",
            "spa": "Español",
            "fre": "Francés",
            "ger": "Alemán",
            "ita": "Italiano",
            "por": "Portugués",
            "rus": "Ruso",
            "jpn": "Japonés",
            "chi": "Chino",
            "kor": "Coreano",
            "ara": "Árabe",
            "hin": "Hindi",
            "dut": "Neerlandés",
            "pol": "Polaco",
            "swe": "Sueco",
            "nor": "Noruego Nynorsk",
            "dan": "Danés",
            "fin": "Finés",
            "cat": "Catalán",
            "zxx": "Mudo",
            "lat": "Español latino",
            "tha": "Tailandés",
            "nob": "Noruego Bokmål",
            "tur": "Turco",
            "gre": "Griego",
            "heb": "Hebreo",
            "rum": "Rumano",
            "ind": "Indonés",
            "vie": "Vietnamita",
            "ukr": "Ucraniano",
            "hun": "Húngaro",
            "cze": "Checo",
            "hrv": "Croata",
            "may": "Malayo",
            "fil": "Filipino",
            "glg": "Gallego",
            "baq": "Vasco",
        },
        "video_codecs": {
            "MPEG4/ISO/AVC": "H.264",
            "MPEGH/ISO/HEVC": "H.265",
            "VP8": "VP8",
            "VP9": "VP9",
            "AV1": "AV1",
            "MPEG2": "MPEG-2",
            "MPEG1": "MPEG-1"
        },
        "audio_codecs": {
            "A_DTS": "DTS",
            "DTS-HD Master Audio": "DTS-HD MA",
            "DTS-X": "DTS-X",
            "AC-3": "AC-3",
            "E-AC-3": "E-AC-3",
            "E-AC-3 JOC": "E-AC-3 JOC",
            "AAC": "AAC LC",
            "FLAC": "FLAC",
            "Vorbis": "Vorbis",
            "Opus": "Opus",
            "MP3": "MP3",
            "PCM": "PCM",
            "TrueHD Atmos": "Dolby Atmos TrueHD",
            "TrueHD": "Dolby TrueHD",
            "AC-3 Dolby Surround EX": "AC-3 EX"
        },
        "subtitle_codecs": {
            "SubRip/SRT": "[SRT]",
            "SubStationAlpha": "[ASS]",
            "HDMV PGS": "[PGS]",
            "VobSub": "[VOB]"
        }
    }

    @classmethod
    def load_config(cls) -> Dict:
        """Load configuration - currently returns default config"""
        return cls.DEFAULT_CONFIG.copy()
