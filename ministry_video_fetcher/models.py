"""
Data Models for Ministry Video Fetcher

Contains dataclasses for video metadata, fetch logs, and preachers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import json


class ContentType(Enum):
    """Classification of video content type."""
    PREACHING = "PREACHING"
    MUSIC = "MUSIC"
    UNKNOWN = "UNKNOWN"


class Language(Enum):
    """Detected language of video content."""
    FRENCH = "FR"
    ENGLISH = "EN"
    UNKNOWN = "UNKNOWN"


@dataclass
class Preacher:
    """
    Represents a preacher/minister whose sermons are tracked.

    Attributes:
        id: Database ID (auto-assigned)
        name: Full name of the preacher
        aliases: List of name variations (auto-generated + custom)
        title: Title/honorific (Apostle, Pastor, Bishop, etc.)
        primary_church: Main church/ministry affiliation
        bio: Brief biography
        is_active: Whether actively tracking this preacher
        created_at: When this preacher was added
        updated_at: Last modification time
        video_count: Number of videos in database (not stored, computed)
    """
    name: str
    aliases: List[str] = field(default_factory=list)
    title: Optional[str] = None
    primary_church: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    video_count: int = 0

    def __post_init__(self):
        """Auto-generate aliases if none provided."""
        if not self.aliases:
            self.aliases = self.generate_aliases(self.name, self.title)

    @staticmethod
    def generate_aliases(name: str, title: Optional[str] = None) -> List[str]:
        """
        Auto-generate French/English name variations.

        Args:
            name: Full name of the preacher
            title: Optional title (Apostle, Pastor, etc.)

        Returns:
            List of name variations for searching
        """
        aliases = [name]
        name_parts = name.split()

        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = name_parts[-1]

            # Add first name and last name separately
            aliases.append(first_name)
            aliases.append(last_name)

            # Title variations in English and French
            title_variations = {
                "Apostle": ["Apostle", "Apotre", "Apôtre"],
                "Pastor": ["Pastor", "Pasteur"],
                "Bishop": ["Bishop", "Évêque", "Eveque"],
                "Prophet": ["Prophet", "Prophète", "Prophete"],
                "Evangelist": ["Evangelist", "Évangéliste", "Evangeliste"],
                "Reverend": ["Reverend", "Révérend", "Rev."],
                "Doctor": ["Doctor", "Dr.", "Docteur"],
            }

            # If title provided, add variations with that title
            if title and title in title_variations:
                for t in title_variations[title]:
                    aliases.append(f"{t} {name}")
                    aliases.append(f"{t} {first_name}")
                    aliases.append(f"{t} {last_name}")
                    aliases.append(f"{t} {first_name} {last_name}")
            else:
                # Add all common title variations
                for title_key, variations in title_variations.items():
                    for t in variations:
                        aliases.append(f"{t} {name}")
                        aliases.append(f"{t} {last_name}")

            # Common suffixes
            for suffix in ["sermon", "predication", "message", "preaching", "teaching", "enseignement"]:
                aliases.append(f"{name} {suffix}")
                aliases.append(f"{last_name} {suffix}")

        # Remove duplicates while preserving order
        seen = set()
        unique_aliases = []
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower not in seen:
                seen.add(alias_lower)
                unique_aliases.append(alias)

        return unique_aliases

    def get_search_queries(self, platform: str = "youtube") -> List[str]:
        """
        Generate platform-specific search queries.

        Args:
            platform: 'youtube' or 'facebook'

        Returns:
            List of search queries optimized for the platform
        """
        queries = []
        name_parts = self.name.split()
        last_name = name_parts[-1] if len(name_parts) > 1 else self.name

        if platform == "youtube":
            # YouTube supports exact match with quotes
            queries.append(f'"{self.name}"')
            queries.append(f'"{self.name}" sermon')
            queries.append(f'"{self.name}" preaching')
            queries.append(f'"{self.name}" predication')
            queries.append(f'"{self.name}" message')
            queries.append(f'"{self.name}" enseignement')

            if self.title:
                queries.append(f'"{self.title} {self.name}"')
                queries.append(f'"{self.title} {last_name}"')

            # Add common title variations
            for t in ["Apostle", "Apotre", "Pastor", "Pasteur"]:
                queries.append(f'"{t} {self.name}"')
                queries.append(f'"{t} {last_name}"')

            if self.primary_church:
                queries.append(f'"{self.primary_church}"')
                queries.append(f'"{self.primary_church}" {last_name}')

        else:  # Facebook
            # Facebook search doesn't use quotes the same way
            queries.append(self.name)
            queries.append(f"{self.name} sermon")
            queries.append(f"{self.name} preaching")
            queries.append(f"{self.name} predication")
            queries.append(f"{self.name} message")
            queries.append(f"{self.name} enseignement")

            if self.title:
                queries.append(f"{self.title} {self.name}")
                queries.append(f"{self.title} {last_name}")

            for t in ["Apostle", "Apotre", "Pastor", "Pasteur"]:
                queries.append(f"{t} {self.name}")

            if self.primary_church:
                queries.append(self.primary_church)

        # Remove duplicates
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)

        return unique_queries

    def get_identity_markers(self) -> dict:
        """
        Generate identity markers for video classification.

        Returns:
            Dictionary with required_names, acceptable_names, and church_names
        """
        name_parts = self.name.split()
        last_name = name_parts[-1] if len(name_parts) > 1 else self.name
        first_name = name_parts[0] if len(name_parts) > 1 else self.name

        required_names = [self.name.lower(), last_name.lower()]

        acceptable_names = []
        for t in ["apostle", "apotre", "apôtre", "pastor", "pasteur",
                  "bishop", "prophet", "evangelist", "reverend"]:
            acceptable_names.append(f"{t} {self.name.lower()}")
            acceptable_names.append(f"{t} {last_name.lower()}")
            acceptable_names.append(f"{t} {first_name.lower()}")

        church_names = []
        if self.primary_church:
            church_names.append(self.primary_church.lower())

        return {
            "required_names": required_names,
            "acceptable_names": acceptable_names,
            "church_names": church_names,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "name": self.name,
            "aliases": json.dumps(self.aliases) if self.aliases else "[]",
            "title": self.title,
            "primary_church": self.primary_church,
            "bio": self.bio,
            "is_active": 1 if self.is_active else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Preacher":
        """Create Preacher from dictionary."""
        aliases = data.get("aliases", [])
        if isinstance(aliases, str):
            try:
                aliases = json.loads(aliases)
            except json.JSONDecodeError:
                aliases = []

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = None

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except ValueError:
                updated_at = None

        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            aliases=aliases,
            title=data.get("title"),
            primary_church=data.get("primary_church"),
            bio=data.get("bio"),
            is_active=bool(data.get("is_active", True)),
            created_at=created_at,
            updated_at=updated_at,
            video_count=data.get("video_count", 0),
        )


@dataclass
class VideoMetadata:
    """
    Represents metadata for a single video (YouTube or Facebook).

    Attributes:
        video_id: Unique video ID (primary key)
        title: Video title
        description: Video description (truncated to 500 chars)
        duration: Duration in seconds
        upload_date: Date when video was uploaded
        view_count: Number of views
        like_count: Number of likes (may be None)
        thumbnail_url: URL to video thumbnail
        channel_name: Name of the channel/page that uploaded the video
        channel_id: Channel/Page ID
        channel_url: URL to the channel/page
        video_url: Full video URL
        platform: Platform source ("youtube" or "facebook")
        content_type: Classification (PREACHING, MUSIC, UNKNOWN)
        confidence_score: How confident the classification is (0.0-1.0)
        needs_review: Flag for uncertain classifications
        language_detected: Detected language (FR, EN, UNKNOWN)
        fetched_at: Timestamp when this video was fetched
        search_query_used: Which search query found this video
    """
    video_id: str
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None  # seconds
    upload_date: Optional[str] = None  # YYYYMMDD format from yt-dlp
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    thumbnail_url: Optional[str] = None
    channel_name: Optional[str] = None
    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    video_url: Optional[str] = None
    platform: str = "youtube"  # "youtube" or "facebook"
    content_type: ContentType = ContentType.UNKNOWN
    confidence_score: float = 0.0
    needs_review: bool = True
    language_detected: Language = Language.UNKNOWN
    fetched_at: datetime = field(default_factory=datetime.now)
    search_query_used: Optional[str] = None
    face_verified: bool = False
    identity_matched: bool = False  # True if preacher's name found in title/description
    channel_trust_level: int = 0    # 0=unknown, 1=known, 2=trusted, 3=verified
    preacher_id: Optional[int] = None  # Reference to preachers table

    def __post_init__(self):
        """Ensure content_type and language are enums."""
        if isinstance(self.content_type, str):
            self.content_type = ContentType(self.content_type)
        if isinstance(self.language_detected, str):
            self.language_detected = Language(self.language_detected)
        if isinstance(self.face_verified, int):
            self.face_verified = bool(self.face_verified)
        if isinstance(self.identity_matched, int):
            self.identity_matched = bool(self.identity_matched)

    @property
    def duration_formatted(self) -> str:
        """Return duration in HH:MM:SS format."""
        if self.duration is None:
            return "Unknown"
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def upload_date_formatted(self) -> Optional[str]:
        """Return upload date in YYYY-MM-DD format."""
        if self.upload_date and len(self.upload_date) == 8:
            return f"{self.upload_date[:4]}-{self.upload_date[4:6]}-{self.upload_date[6:]}"
        return self.upload_date

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "upload_date": self.upload_date,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "thumbnail_url": self.thumbnail_url,
            "channel_name": self.channel_name,
            "channel_id": self.channel_id,
            "channel_url": self.channel_url,
            "video_url": self.video_url,
            "platform": self.platform,
            "content_type": self.content_type.value,
            "confidence_score": self.confidence_score,
            "needs_review": self.needs_review,
            "language_detected": self.language_detected.value,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "search_query_used": self.search_query_used,
            "face_verified": self.face_verified,
            "identity_matched": self.identity_matched,
            "channel_trust_level": self.channel_trust_level,
            "preacher_id": self.preacher_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VideoMetadata":
        """Create VideoMetadata from dictionary."""
        # Handle datetime conversion
        fetched_at = data.get("fetched_at")
        if isinstance(fetched_at, str):
            try:
                fetched_at = datetime.fromisoformat(fetched_at)
            except ValueError:
                fetched_at = datetime.now()
        elif fetched_at is None:
            fetched_at = datetime.now()

        # Handle enum conversions
        content_type = data.get("content_type", "UNKNOWN")
        if isinstance(content_type, str):
            content_type = ContentType(content_type)

        language = data.get("language_detected", "UNKNOWN")
        if isinstance(language, str):
            language = Language(language)

        return cls(
            video_id=data["video_id"],
            title=data.get("title", ""),
            description=data.get("description"),
            duration=data.get("duration"),
            upload_date=data.get("upload_date"),
            view_count=data.get("view_count"),
            like_count=data.get("like_count"),
            thumbnail_url=data.get("thumbnail_url"),
            channel_name=data.get("channel_name"),
            channel_id=data.get("channel_id"),
            channel_url=data.get("channel_url"),
            video_url=data.get("video_url"),
            platform=data.get("platform", "youtube"),
            content_type=content_type,
            confidence_score=data.get("confidence_score", 0.0),
            needs_review=data.get("needs_review", True),
            language_detected=language,
            fetched_at=fetched_at,
            search_query_used=data.get("search_query_used"),
            face_verified=data.get("face_verified", False),
            identity_matched=data.get("identity_matched", False),
            channel_trust_level=data.get("channel_trust_level", 0),
            preacher_id=data.get("preacher_id"),
        )

    @classmethod
    def from_ytdlp(cls, info: dict, search_query: Optional[str] = None,
                   preacher_id: Optional[int] = None) -> "VideoMetadata":
        """
        Create VideoMetadata from yt-dlp extracted info.

        Args:
            info: Dictionary returned by yt-dlp extract_info
            search_query: The search query that found this video
            preacher_id: The preacher this video is associated with

        Returns:
            VideoMetadata instance
        """
        video_id = info.get("id", "")

        # Build video URL and detect platform
        video_url = info.get("webpage_url") or info.get("url") or ""
        extractor = info.get("extractor", "").lower()

        # Detect platform from extractor or URL
        if "facebook" in extractor or "facebook.com" in video_url.lower():
            platform = "facebook"
        else:
            platform = "youtube"

        # Build fallback video URL based on platform
        if not video_url and video_id:
            if platform == "facebook":
                video_url = f"https://www.facebook.com/watch?v={video_id}"
            else:
                video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Build channel/page URL
        channel_id = info.get("channel_id") or info.get("uploader_id")
        channel_url = info.get("channel_url") or info.get("uploader_url")
        if not channel_url and channel_id:
            if platform == "facebook":
                channel_url = f"https://www.facebook.com/{channel_id}"
            else:
                channel_url = f"https://www.youtube.com/channel/{channel_id}"

        # Truncate description
        description = info.get("description", "")
        if description and len(description) > 500:
            description = description[:497] + "..."

        return cls(
            video_id=video_id,
            title=info.get("title", ""),
            description=description,
            duration=info.get("duration"),
            upload_date=info.get("upload_date"),
            view_count=info.get("view_count"),
            like_count=info.get("like_count"),
            thumbnail_url=info.get("thumbnail"),
            channel_name=info.get("channel") or info.get("uploader"),
            channel_id=channel_id,
            channel_url=channel_url,
            video_url=video_url,
            platform=platform,
            fetched_at=datetime.now(),
            search_query_used=search_query,
            preacher_id=preacher_id,
        )


@dataclass
class FetchLog:
    """
    Represents a log entry for a fetch operation.

    Attributes:
        id: Auto-incremented ID
        fetch_timestamp: When the fetch occurred
        query_used: The search query or channel URL
        videos_found: Total videos found
        videos_added: New videos added to database
        videos_skipped: Duplicates skipped
        music_excluded: Music videos excluded
        errors_count: Number of errors encountered
        error_messages: Details of any errors
    """
    query_used: str
    videos_found: int = 0
    videos_added: int = 0
    videos_skipped: int = 0
    music_excluded: int = 0
    errors_count: int = 0
    error_messages: Optional[str] = None
    fetch_timestamp: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "fetch_timestamp": self.fetch_timestamp.isoformat(),
            "query_used": self.query_used,
            "videos_found": self.videos_found,
            "videos_added": self.videos_added,
            "videos_skipped": self.videos_skipped,
            "music_excluded": self.music_excluded,
            "errors_count": self.errors_count,
            "error_messages": self.error_messages,
        }


@dataclass
class FetchSummary:
    """
    Summary of a complete fetch operation across all queries.
    """
    total_videos_found: int = 0
    duplicates_removed: int = 0
    music_excluded: int = 0
    low_confidence_excluded: int = 0  # NEW: Videos rejected due to low confidence
    unknown_channel_rejected: int = 0  # NEW: Videos from unknown channels without identity
    new_videos_added: int = 0
    total_in_database: int = 0
    videos_needing_review: int = 0
    unique_channels: int = 0
    oldest_video_date: Optional[str] = None
    newest_video_date: Optional[str] = None
    total_preaching_hours: float = 0.0
    top_channels: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def print_summary(self):
        """Print a formatted summary."""
        print("\n" + "=" * 60)
        print("FETCH SUMMARY")
        print("=" * 60)
        print(f"Total videos found across all searches: {self.total_videos_found}")
        print(f"Duplicates removed:                     {self.duplicates_removed}")
        print(f"Music videos excluded:                  {self.music_excluded}")
        print(f"Low confidence excluded:                {self.low_confidence_excluded}")
        print(f"Unknown channel rejected:               {self.unknown_channel_rejected}")
        print(f"New preaching videos added:             {self.new_videos_added}")
        print("-" * 60)
        print(f"Total preaching videos in database:     {self.total_in_database}")
        print(f"Videos flagged for review:              {self.videos_needing_review}")
        print(f"Unique channels represented:            {self.unique_channels}")
        print("-" * 60)

        if self.oldest_video_date and self.newest_video_date:
            print(f"Date range: {self.oldest_video_date} to {self.newest_video_date}")

        hours = int(self.total_preaching_hours)
        minutes = int((self.total_preaching_hours - hours) * 60)
        print(f"Total preaching hours:                  {hours}h {minutes}m")

        if self.top_channels:
            print("-" * 60)
            print("Top 5 channels by video count:")
            for i, (channel, count) in enumerate(self.top_channels[:5], 1):
                print(f"  {i}. {channel}: {count} videos")

        if self.errors:
            print("-" * 60)
            print(f"Errors encountered: {len(self.errors)}")
            for error in self.errors[:5]:
                print(f"  - {error}")

        print("=" * 60 + "\n")
