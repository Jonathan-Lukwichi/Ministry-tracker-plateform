"""
Configuration for Ministry Video Fetcher

Contains search queries, classification keywords, and settings for fetching
videos from YouTube and Facebook. Supports dynamic multi-preacher configuration.
"""

from typing import List, Dict, Optional

# =============================================================================
# PLATFORM CONSTANTS
# =============================================================================

PLATFORM_YOUTUBE = "youtube"
PLATFORM_FACEBOOK = "facebook"

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
# FACEBOOK PAGES (FETCH ALL VIDEOS)
# =============================================================================

FACEBOOK_PAGES: List[Dict] = [
    {
        "name": "Ramah Full Gospel Church Pretoria",
        "url": "https://www.facebook.com/ramahfgpta/videos",
        "page_id": "ramahfgpta",
    },
    # Discovered pages will be added here automatically
]

# =============================================================================
# FACEBOOK SEARCH QUERIES
# =============================================================================

FACEBOOK_SEARCH_QUERIES: List[str] = [
    # === EXACT NAME MATCHES WITH TITLES ===
    # English titles
    "Apostle Narcisse Majila",
    "Pastor Narcisse Majila",
    "Prophet Narcisse Majila",
    "Bishop Narcisse Majila",
    "Reverend Narcisse Majila",

    # French titles (with and without accents)
    "Apotre Narcisse Majila",
    "Apôtre Narcisse Majila",
    "Pasteur Narcisse Majila",
    "Prophète Narcisse Majila",
    "Prophete Narcisse Majila",
    "Évêque Narcisse Majila",
    "Eveque Narcisse Majila",

    # === NAME ONLY (various spellings) ===
    "Narcisse Majila",
    "Naricisse Majila",  # Common misspelling
    "Narcis Majila",
    "N. Majila",

    # === FRENCH COMBINATIONS (prédication/enseignement) ===
    "Narcisse Majila predication",
    "Narcisse Majila prédication",
    "Narcisse Majila enseignement",
    "Narcisse Majila message",
    "Narcisse Majila culte",
    "Narcisse Majila parole",
    "Narcisse Majila priere",
    "Narcisse Majila prière",
    "Narcisse Majila delivrance",
    "Narcisse Majila délivrance",
    "Narcisse Majila guerison",
    "Narcisse Majila guérison",
    "Narcisse Majila prophetie",
    "Narcisse Majila prophétie",
    "Narcisse Majila veillee",
    "Narcisse Majila veillée",

    # French with titles
    "Apotre Majila predication",
    "Apôtre Majila prédication",
    "Pasteur Majila message",
    "Pasteur Majila enseignement",

    # === ENGLISH COMBINATIONS ===
    "Narcisse Majila sermon",
    "Narcisse Majila preaching",
    "Narcisse Majila teaching",
    "Narcisse Majila message",
    "Narcisse Majila prayer",
    "Narcisse Majila deliverance",
    "Narcisse Majila healing",
    "Narcisse Majila prophecy",
    "Narcisse Majila revival",
    "Narcisse Majila crusade",
    "Narcisse Majila conference",

    # English with titles
    "Apostle Majila sermon",
    "Apostle Majila preaching",
    "Pastor Majila message",

    # === CHURCH-RELATED ===
    "Ramah Full Gospel Church Pretoria",
    "Ramah Church Pretoria Narcisse",
    "Ramah Church Narcisse Majila",
    "RFGC Pretoria Majila",
    "Ramah FGC Narcisse",

    # === EVENT-BASED QUERIES ===
    "Narcisse Majila 2024",
    "Narcisse Majila 2023",
    "Narcisse Majila live",
    "Narcisse Majila direct",
    "Majila en direct",
]

# =============================================================================
# FACEBOOK FETCHER SETTINGS
# =============================================================================

FACEBOOK_FETCHER_CONFIG = {
    # Rate limiting (Facebook is stricter)
    "request_delay": 3.0,        # Seconds between requests (higher for Facebook)
    "retry_count": 3,            # Number of retries on failure
    "retry_delay": 5.0,          # Initial delay between retries

    # Cookies file for authentication
    # To export cookies from your browser:
    # 1. Install "Get cookies.txt LOCALLY" extension in Chrome/Firefox
    # 2. Log in to Facebook in your browser
    # 3. Go to facebook.com and click the extension
    # 4. Click "Export" and save as "facebook_cookies.txt" in the ministry_video_fetcher folder
    # 5. The file path below will automatically use it
    "cookies_file": "facebook_cookies.txt",

    # yt-dlp options for Facebook
    "quiet": True,
    "no_warnings": True,
    "ignoreerrors": True,

    # Max results per search/page
    "max_results_per_query": 50,  # Facebook returns fewer results typically

    # Hybrid mode settings (NEW)
    "use_graph_api": True,        # Enable Graph API for discovery
    "use_ytdlp_fallback": True,   # Use yt-dlp for video URL extraction
    "prefer_graph_api": True,     # Prefer Graph API when available
}

# =============================================================================
# FACEBOOK GRAPH API SETTINGS (NEW - Hybrid Approach)
# =============================================================================

FACEBOOK_GRAPH_API_CONFIG = {
    # API Version and Base URL
    "api_version": "v18.0",
    "base_url": "https://graph.facebook.com/v18.0",

    # Token management
    "token_file": "fb_token.json",  # Persisted token storage (gitignored)
    "token_refresh_days_before_expiry": 7,  # Refresh 7 days before expiry

    # App credentials - USER MUST FILL IN after creating Facebook Developer App
    # 1. Go to https://developers.facebook.com/
    # 2. Create a Business app
    # 3. Copy App ID and App Secret here
    "app_id": "",          # From Facebook Developer Console
    "app_secret": "",      # From Facebook Developer Console
    "access_token": "",    # Page Access Token (long-lived, 60 days)

    # Page IDs to fetch videos from
    # These are the Facebook page usernames or numeric IDs
    "page_ids": [
        "ramahfgpta",  # Ramah Full Gospel Church Pretoria
        "ApostleNarcisseMajilaMinistries",  # Apostle's official ministry page
        # Add more page IDs as discovered
    ],

    # Rate limiting (Graph API is more lenient)
    "requests_per_hour": 200,    # Graph API rate limit
    "request_delay": 0.5,        # Delay between requests (seconds)
    "retry_count": 3,
    "retry_delay": 2.0,

    # Video fields to fetch from Graph API
    "video_fields": [
        "id",
        "title",
        "description",
        "created_time",
        "length",           # Duration in seconds
        "thumbnails",       # Array of thumbnail URLs
        "permalink_url",    # Facebook watch URL
        "from",             # Page that posted
        "live_status",      # Was it a live video?
    ],

    # Filtering
    "min_duration_seconds": 600,  # Ignore videos < 10 minutes (likely not sermons)
    "max_results_per_page": 100,  # Pagination limit
}

# =============================================================================
# FACEBOOK AGENT SETTINGS (Playwright-based automated discovery)
# =============================================================================

FACEBOOK_AGENT_CONFIG = {
    # Browser automation settings
    "headless": False,              # Run browser in visible mode for debugging
    "slow_mo": 100,                 # Slow down Playwright actions by this many ms
    "timeout": 60000,               # Default timeout for page operations (60s)

    # Scrolling and pagination
    "max_scroll_iterations": 10,    # Max number of scroll attempts per search
    "scroll_delay": 2.0,            # Seconds to wait after each scroll for content to load
    "scroll_amount": 800,           # Pixels to scroll each iteration

    # Rate limiting
    "max_videos_per_search": 50,    # Max videos to extract per search query
    "delay_between_videos": 1.5,    # Seconds delay between processing videos
    "delay_between_searches": 5.0,  # Seconds delay between search queries

    # Authentication
    "cookies_file": "facebook_cookies.txt",  # Browser cookies for Facebook login

    # Channel learning
    "discovered_channels_file": "discovered_channels.json",  # Stores discovered channels
    "remember_channels": True,       # Remember channels where preacher appears

    # Search configuration
    "use_facebook_watch": True,      # Search on Facebook Watch for videos
    "search_base_url": "https://www.facebook.com/watch/search/?q=",

    # Validation
    "require_face_verification": False,  # Don't require face match (use title/description matching)
    "min_video_duration": 600,           # Minimum duration (10 min) for sermons

    # User agent
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# =============================================================================
# SEARCH QUERIES (YOUTUBE)
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

# =============================================================================
# DYNAMIC SEARCH QUERY GENERATOR
# =============================================================================


def generate_search_queries(
    name: str,
    title: Optional[str] = None,
    primary_church: Optional[str] = None,
    platform: str = "youtube",
    include_aliases: Optional[List[str]] = None
) -> List[str]:
    """
    Generate platform-specific search queries from a preacher's name.

    Generates comprehensive bilingual queries in both English and French
    for maximum coverage across international ministries.

    Args:
        name: Full name of the preacher (e.g., "Narcisse Majila")
        title: Optional title (e.g., "Apostle", "Pastor")
        primary_church: Optional church name
        platform: 'youtube' or 'facebook'
        include_aliases: Optional list of name aliases/misspellings

    Returns:
        List of search queries optimized for the platform
    """
    queries = []
    name_parts = name.split()
    last_name = name_parts[-1] if len(name_parts) > 1 else name
    first_name = name_parts[0] if len(name_parts) > 1 else name

    # Title variations in English and French (with and without accents)
    title_pairs = [
        ("Apostle", "Apotre", "Apôtre"),
        ("Pastor", "Pasteur", "Pasteur"),
        ("Bishop", "Eveque", "Évêque"),
        ("Prophet", "Prophete", "Prophète"),
        ("Evangelist", "Evangeliste", "Évangéliste"),
        ("Reverend", "Reverend", "Révérend"),
        ("Dr.", "Dr.", "Dr."),
    ]

    # Preaching keywords in English and French (with and without accents)
    keywords_en = [
        "sermon", "preaching", "teaching", "message", "deliverance",
        "healing", "prophecy", "prayer", "revival", "crusade",
        "conference", "service", "worship"
    ]
    keywords_fr = [
        "predication", "prédication", "enseignement", "message",
        "delivrance", "délivrance", "guerison", "guérison",
        "prophetie", "prophétie", "priere", "prière",
        "reveil", "réveil", "croisade", "conference", "conférence",
        "culte", "adoration", "louange"
    ]

    # Event-related keywords
    event_keywords = ["2024", "2023", "2025", "live", "direct", "en direct"]

    if platform == "youtube":
        # YouTube supports exact match with quotes
        queries.append(f'"{name}"')

        # With preaching keywords (both languages)
        for kw in keywords_en:
            queries.append(f'"{name}" {kw}')
        for kw in keywords_fr:
            queries.append(f'"{name}" {kw}')

        # With title variations
        if title:
            queries.append(f'"{title} {name}"')
            queries.append(f'"{title} {last_name}"')

        # Add common title variations (all versions)
        for titles in title_pairs:
            for t in titles:
                queries.append(f'"{t} {name}"')
                queries.append(f'"{t} {last_name}"')

        # Church-related queries
        if primary_church:
            queries.append(f'"{primary_church}"')
            queries.append(f'"{primary_church}" {last_name}')
            queries.append(f'"{primary_church}" {name}')

        # Add aliases/misspellings
        if include_aliases:
            for alias in include_aliases:
                queries.append(f'"{alias}"')
                for kw in keywords_en[:3] + keywords_fr[:3]:
                    queries.append(f'"{alias}" {kw}')

    else:  # Facebook
        # Facebook search doesn't use quotes the same way
        queries.append(name)

        # With preaching keywords (both English and French)
        for kw in keywords_en:
            queries.append(f"{name} {kw}")
        for kw in keywords_fr:
            queries.append(f"{name} {kw}")

        # With title variations (all versions - English, French no accent, French with accent)
        if title:
            queries.append(f"{title} {name}")
            queries.append(f"{title} {last_name}")

        # Add all title variations for comprehensive coverage
        for titles in title_pairs:
            for t in titles:
                queries.append(f"{t} {name}")
                queries.append(f"{t} {last_name}")

        # Event-based queries (for finding recent content)
        for event_kw in event_keywords:
            queries.append(f"{name} {event_kw}")
            queries.append(f"{last_name} {event_kw}")

        # Church-related queries
        if primary_church:
            queries.append(primary_church)
            queries.append(f"{primary_church} {last_name}")
            queries.append(f"{primary_church} {name}")

        # Add aliases/misspellings (important for Facebook)
        if include_aliases:
            for alias in include_aliases:
                queries.append(alias)
                for kw in keywords_en[:3] + keywords_fr[:3]:
                    queries.append(f"{alias} {kw}")

        # Special Facebook queries with "video" keyword
        queries.append(f"{name} video")
        queries.append(f"{name} vidéo")
        queries.append(f"{name} facebook live")

    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)

    return unique_queries


def generate_identity_markers(
    name: str,
    title: Optional[str] = None,
    primary_church: Optional[str] = None,
    aliases: Optional[List[str]] = None
) -> Dict:
    """
    Generate identity markers for video classification from preacher info.

    Args:
        name: Full name of the preacher
        title: Optional title
        primary_church: Optional church name
        aliases: Optional list of name aliases

    Returns:
        Dictionary with required_names, acceptable_names, and church_names
    """
    name_parts = name.split()
    last_name = name_parts[-1] if len(name_parts) > 1 else name
    first_name = name_parts[0] if len(name_parts) > 1 else name

    # Required names (strongest match)
    required_names = [name.lower(), last_name.lower()]
    if aliases:
        for alias in aliases:
            if alias.lower() not in required_names:
                required_names.append(alias.lower())

    # Acceptable names (good match with titles)
    acceptable_names = []
    for t in ["apostle", "apotre", "apôtre", "pastor", "pasteur",
              "bishop", "prophet", "evangelist", "reverend", "dr."]:
        acceptable_names.append(f"{t} {name.lower()}")
        acceptable_names.append(f"{t} {last_name.lower()}")
        acceptable_names.append(f"{t} {first_name.lower()}")

    # Additional descriptors
    for desc in ["man of god", "servant of god", "serviteur de dieu", "homme de dieu"]:
        acceptable_names.append(f"{desc} {name.lower()}")
        acceptable_names.append(f"{desc} {last_name.lower()}")

    # Church names
    church_names = []
    if primary_church:
        church_names.append(primary_church.lower())
        # Also add abbreviated versions
        church_words = primary_church.lower().split()
        if len(church_words) > 2:
            # Create acronym
            acronym = "".join(w[0] for w in church_words if w not in ["of", "the", "and"])
            church_names.append(acronym)

    return {
        "required_names": required_names,
        "acceptable_names": acceptable_names,
        "church_names": church_names,
        "strict_mode": True,
        "require_name_not_just_church": True,
    }


def get_photos_directory(preacher_id: int) -> str:
    """
    Get the photos directory path for a specific preacher.

    Args:
        preacher_id: ID of the preacher

    Returns:
        Path to the preacher's photos directory
    """
    import os
    base_dir = FACE_RECOGNITION_CONFIG.get("photos_dir", "photos")
    return os.path.join(base_dir, f"preacher_{preacher_id}")
