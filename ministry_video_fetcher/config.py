"""
Configuration for Ministry Video Fetcher

Contains search queries, classification keywords, and settings for fetching
videos of Apostle Narcisse Majila from YouTube.
"""

from typing import List, Dict

# =============================================================================
# TARGET PERSON CONFIGURATION
# =============================================================================

TARGET_PERSON = {
    "name": "Apostle Narcisse Majila",
    "aliases": [
        "Narcisse Majila",
        "Apotre Narcisse Majila",
        "Apôtre Narcisse Majila",
        "Pastor Narcisse Majila",
        "Pasteur Narcisse Majila",
    ],
    "primary_church": "Ramah Full Gospel Church Pretoria",
}

# =============================================================================
# PRIMARY CHANNEL (FETCH ALL VIDEOS)
# =============================================================================

PRIMARY_CHANNEL = {
    "name": "Ramah Full Gospel Church Pretoria",
    "url": "https://www.youtube.com/@RamahFullGospelChurchPretoria",
    "channel_id": "@RamahFullGospelChurchPretoria",
}

# =============================================================================
# SEARCH QUERIES
# =============================================================================

SEARCH_QUERIES: List[str] = [
    # Exact name matches with titles
    '"Apostle Narcisse Majila"',
    '"Apotre Narcisse Majila"',
    '"Pasteur Narcisse Majila"',
    '"Pastor Narcisse Majila"',

    # Exact name matches without titles
    '"Narcisse Majila"',
    '"Naricisse Majila"', # Found in photo file names

    # English combinations with preaching keywords
    '"Apostle Narcisse Majila" sermon',
    '"Apostle Narcisse Majila" preaching',
    '"Apostle Narcisse Majila" teaching',
    '"Narcisse Majila" sermon',
    '"Narcisse Majila" message',

    # French combinations with preaching keywords
    '"Apotre Narcisse Majila" predication',
    '"Apotre Narcisse Majila" enseignement',
    '"Apotre Narcisse Majila" message',
    '"Apotre Narcisse Majila" culte',
    '"Narcisse Majila" predication',
    '"Narcisse Majila" enseignement',

    # Queries with the alternative spelling
    '"Naricisse Majila" sermon',
    '"Naricisse Majila" predication',
]

# Maximum results per search query
MAX_RESULTS_PER_QUERY = 100

# =============================================================================
# CONTENT CLASSIFICATION KEYWORDS
# =============================================================================

# Keywords indicating PREACHING content (English)
PREACHING_KEYWORDS_EN: List[str] = [
    "preaching", "sermon", "message", "teaching", "word", "prophecy",
    "prayer", "deliverance", "faith", "healing", "anointing",
    "sunday service", "conference", "crusade", "revival", "camp meeting",
    "bible study", "word of god", "holy spirit", "salvation", "grace",
    "testimony", "miracles", "breakthrough", "prophetic", "apostolic",
    "part 1", "part 2", "part 3", "pt 1", "pt 2", "pt 3",
    "session 1", "session 2", "day 1", "day 2", "night 1", "night 2",
    "morning service", "evening service", "night vigil",
]

# Keywords indicating PREACHING content (French)
PREACHING_KEYWORDS_FR: List[str] = [
    "predication", "message", "enseignement", "parole", "prophetie",
    "priere", "delivrance", "foi", "guerison", "onction",
    "culte", "conference", "croisade", "reveil", "camp",
    "etude biblique", "parole de dieu", "saint esprit", "salut", "grace",
    "temoignage", "miracles", "percee", "prophetique", "apostolique",
    "partie 1", "partie 2", "partie 3",
    "session 1", "session 2", "jour 1", "jour 2", "nuit 1", "nuit 2",
    "culte du matin", "culte du soir", "veillee",
]

# Keywords indicating MUSIC content (to EXCLUDE)
MUSIC_KEYWORDS: List[str] = [
    # English
    "music", "song", "singing", "worship song", "album", "lyrics",
    "official video", "music video", "live performance", "concert",
    "praise and worship", "worship medley", "gospel song",
    "audio", "mp3", "single", "track",
    # French
    "musique", "chanson", "chant", "louange", "album", "paroles",
    "clip officiel", "clip video", "spectacle", "concert",
    "louange et adoration", "medley", "cantique",
    # Common music indicators
    "feat.", "ft.", "featuring", "prod.", "remix",
]

# Keywords that strongly indicate it's a music video (high confidence exclude)
STRONG_MUSIC_INDICATORS: List[str] = [
    "official video", "clip officiel", "music video", "clip video",
    "album", "single", "track", "audio only", "lyrics video",
    "feat.", "ft.", "remix", "prod by", "produced by",
]

# =============================================================================
# CLASSIFICATION RULES
# =============================================================================

CLASSIFICATION_CONFIG = {
    # Duration thresholds (in seconds)
    "min_sermon_duration": 1800,     # 30 minutes - minimum for a sermon
    "likely_sermon_duration": 2700,  # 45 minutes - very likely a sermon
    "max_music_duration": 600,       # 10 minutes - if no preaching keywords, likely music
    "short_clip_duration": 240,      # 4 minutes - very short, likely music/clip

    # Confidence thresholds
    "high_confidence": 0.85,
    "medium_confidence": 0.65,
    "low_confidence": 0.45,

    # If confidence below this, flag for review
    "review_threshold": 0.60,
}

# =============================================================================
# LANGUAGE DETECTION KEYWORDS
# =============================================================================

FRENCH_INDICATORS: List[str] = [
    "predication", "message", "enseignement", "culte", "priere",
    "delivrance", "guerison", "parole", "dieu", "eglise",
    "partie", "jour", "nuit", "dimanche", "vendredi",
    "apotre", "pasteur", "frere", "soeur",
    "le", "la", "les", "du", "de", "des", "et", "ou", "avec",
]

ENGLISH_INDICATORS: List[str] = [
    "preaching", "sermon", "teaching", "service", "prayer",
    "deliverance", "healing", "word", "god", "church",
    "part", "day", "night", "sunday", "friday",
    "apostle", "pastor", "brother", "sister",
    "the", "and", "of", "in", "for", "with", "by",
]

# =============================================================================
# FETCHER SETTINGS
# =============================================================================

FETCHER_CONFIG = {
    # Rate limiting
    "request_delay": 1.0,        # Seconds between requests
    "retry_count": 3,            # Number of retries on failure
    "retry_delay": 2.0,          # Initial delay between retries (exponential backoff)

    # yt-dlp options
    "extract_flat": True,        # Don't download, just extract metadata
    "quiet": True,               # Suppress yt-dlp output
    "no_warnings": True,         # Suppress warnings
    "ignoreerrors": True,        # Continue on errors

    # Data limits
    "max_description_length": 500,  # Truncate descriptions
}

# =============================================================================
# DATABASE SETTINGS
# =============================================================================

DATABASE_CONFIG = {
    "db_path": "ministry_videos.db",
    "backup_enabled": True,
}

# =============================================================================
# EXPORT SETTINGS
# =============================================================================

EXPORT_CONFIG = {
    "csv_filename": "ministry_videos_export.csv",
    "date_format": "%Y-%m-%d",
    "datetime_format": "%Y-%m-%d %H:%M:%S",
}

# =============================================================================
# FACE RECOGNITION SETTINGS
# =============================================================================

FACE_RECOGNITION_CONFIG = {
    # Model settings
    "model_name": "VGG-Face",  # Options: VGG-Face, Facenet, Facenet512, ArcFace, OpenFace
    "detector_backend": "opencv",  # Options: opencv, ssd, dlib, mtcnn, retinaface
    "distance_metric": "cosine",  # Options: cosine, euclidean, euclidean_l2
    "distance_threshold": 0.40,  # Lower = stricter matching (0.4 is good for VGG-Face)

    # Frame extraction settings
    "enable_frame_extraction": True,  # Extract frames from video for deeper analysis
    "num_frames": 5,  # Number of frames to extract
    "frame_interval_seconds": 10,  # Time between frames
    "video_segment_duration": 60,  # Download first N seconds of video

    # Reference photos directory
    "photos_dir": "photos",
}

# =============================================================================
# STRICT CHANNELS - Require face verification
# =============================================================================

# Videos from these channels MUST have face verification to be classified as PREACHING.
# If face is not detected, video will be flagged for review.
STRICT_CHANNELS: List[str] = [
    # Primary church channel - may have videos of other speakers
    "Ramah Full Gospel Church Pretoria",
    "RamahFullGospelChurchPretoria",
    "@RamahFullGospelChurchPretoria",

    # Add other channels that may have multiple speakers
    # "Another Church Channel",
]

# Channels that are known to only feature the target person (skip face verification)
TRUSTED_CHANNELS: List[str] = [
    # Add channels that exclusively feature Apostle Narcisse Majila
]

# =============================================================================
# IDENTITY MARKERS - Required for video acceptance
# =============================================================================

IDENTITY_MARKERS = {
    # These names MUST appear in video title/description (strongest match)
    "required_names": [
        "narcisse majila",
        "naricisse majila",  # Common misspelling
    ],

    # Alternative acceptable names (good match)
    "acceptable_names": [
        "apostle narcisse",
        "apotre narcisse",
        "apôtre narcisse",
        "pastor narcisse",
        "pasteur narcisse",
        "apostle majila",
        "apotre majila",
        "pastor majila",
        "pasteur majila",
        "man of god narcisse",
        "servant of god narcisse",
        "serviteur de dieu narcisse",
    ],

    # Church names - NO LONGER SUFFICIENT for identity match
    # These are only used for context boosting, NOT as identity proof
    "church_names": [
        "ramah full gospel",
        "ramah pretoria",
        "rfgc pretoria",
        "ramah church",
    ],

    # If True, videos WITHOUT identity markers will be rejected (unless face verified)
    "strict_mode": True,

    # NEW: Require the apostle's NAME, not just church name
    # Church name alone is NOT enough to accept a video
    "require_name_not_just_church": True,
}

# =============================================================================
# CHANNEL TRUST LEVELS
# =============================================================================

CHANNEL_TRUST_LEVELS = {
    # Level 3: Verified channels - ONLY Apostle's content, skip all validation
    "verified": [
        # Add channels that EXCLUSIVELY feature Apostle Narcisse Majila
        # Example: His personal channel if he has one
    ],

    # Level 2: Trusted channels - known churches, require identity OR face
    "trusted": [
        "ramah full gospel church pretoria",
        "@ramahfullgospelchurchpretoria",
        "ramahfullgospelchurchpretoria",
    ],

    # Level 1: Known channels - churches where he preaches, require identity AND face
    "known": [
        # Add channels of churches where he has preached
        # but that also feature other speakers
    ],

    # Level 0: Unknown channels (all others) - strictest validation
    # - Require identity markers in title/description
    # - Require face verification (if DeepFace available)
}

# =============================================================================
# FACE VERIFICATION REQUIREMENTS
# =============================================================================

FACE_VERIFICATION_REQUIREMENTS = {
    # Minimum face confidence to count as verified
    "min_confidence": 0.70,

    # Require face verification for unknown channels
    "required_for_unknown_channels": True,

    # Allow classification if DeepFace unavailable (fall back to other signals)
    "allow_deepface_bypass": True,
}

# =============================================================================
# STORAGE THRESHOLDS
# =============================================================================

STORAGE_CONFIG = {
    # Minimum confidence to store a video (below this = skip entirely)
    "min_storage_confidence": 0.50,

    # Confidence above which video is auto-accepted without review
    "auto_accept_confidence": 0.85,

    # Confidence threshold for flagging for review
    "review_threshold": 0.70,
}
