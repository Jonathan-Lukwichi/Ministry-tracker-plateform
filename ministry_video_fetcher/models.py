"""
Data Models for Ministry Video Fetcher

Contains dataclasses for video metadata and fetch logs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


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
class VideoMetadata:
    """
    Represents metadata for a single YouTube video.

    Attributes:
        video_id: Unique YouTube video ID (primary key)
        title: Video title
        description: Video description (truncated to 500 chars)
        duration: Duration in seconds
        upload_date: Date when video was uploaded
        view_count: Number of views
        like_count: Number of likes (may be None)
        thumbnail_url: URL to video thumbnail
        channel_name: Name of the channel that uploaded the video
        channel_id: YouTube channel ID
        channel_url: URL to the channel
        video_url: Full YouTube video URL
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
    content_type: ContentType = ContentType.UNKNOWN
    confidence_score: float = 0.0
    needs_review: bool = True
    language_detected: Language = Language.UNKNOWN
    fetched_at: datetime = field(default_factory=datetime.now)
    search_query_used: Optional[str] = None
    face_verified: bool = False
    identity_matched: bool = False  # NEW: True if apostle's name/church found in title/description
    channel_trust_level: int = 0    # NEW: 0=unknown, 1=known, 2=trusted, 3=verified

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
            "content_type": self.content_type.value,
            "confidence_score": self.confidence_score,
            "needs_review": self.needs_review,
            "language_detected": self.language_detected.value,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "search_query_used": self.search_query_used,
            "face_verified": self.face_verified,
            "identity_matched": self.identity_matched,
            "channel_trust_level": self.channel_trust_level,
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
            content_type=content_type,
            confidence_score=data.get("confidence_score", 0.0),
            needs_review=data.get("needs_review", True),
            language_detected=language,
            fetched_at=fetched_at,
            search_query_used=data.get("search_query_used"),
            face_verified=data.get("face_verified", False),
            identity_matched=data.get("identity_matched", False),
            channel_trust_level=data.get("channel_trust_level", 0),
        )

    @classmethod
    def from_ytdlp(cls, info: dict, search_query: Optional[str] = None) -> "VideoMetadata":
        """
        Create VideoMetadata from yt-dlp extracted info.

        Args:
            info: Dictionary returned by yt-dlp extract_info
            search_query: The search query that found this video

        Returns:
            VideoMetadata instance
        """
        video_id = info.get("id", "")

        # Build video URL
        video_url = info.get("webpage_url") or info.get("url")
        if not video_url and video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Build channel URL
        channel_id = info.get("channel_id") or info.get("uploader_id")
        channel_url = info.get("channel_url") or info.get("uploader_url")
        if not channel_url and channel_id:
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
            fetched_at=datetime.now(),
            search_query_used=search_query,
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
