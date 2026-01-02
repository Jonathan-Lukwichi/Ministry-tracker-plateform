"""
Video Fetcher for Ministry Video Fetcher

Uses yt-dlp to fetch video metadata from YouTube searches and channels.
"""

import time
from datetime import datetime
from typing import List, Optional, Dict, Set
import logging

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

from models import VideoMetadata, FetchLog, FetchSummary, ContentType
from classifier import ContentClassifier
from database import Database
from config import (
    SEARCH_QUERIES,
    PRIMARY_CHANNEL,
    MAX_RESULTS_PER_QUERY,
    FETCHER_CONFIG,
    STORAGE_CONFIG,
    IDENTITY_MARKERS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VideoFetcher:
    """
    Fetches video metadata from YouTube using yt-dlp.

    Supports both search queries and channel scraping.
    """

    def __init__(self, db: Optional[Database] = None):
        """
        Initialize the fetcher.

        Args:
            db: Database instance. Creates new one if None.
        """
        self.db = db or Database()
        self.classifier = ContentClassifier()
        self.config = FETCHER_CONFIG

        # Track seen video IDs to avoid duplicate processing
        self._seen_ids: Set[str] = set()

        # yt-dlp options
        self._ydl_opts = {
            "quiet": self.config["quiet"],
            "no_warnings": self.config["no_warnings"],
            "ignoreerrors": self.config["ignoreerrors"],
            "extract_flat": False,  # Get full metadata
            "skip_download": True,  # Don't download videos
        }

    def fetch_all(self) -> FetchSummary:
        """
        Run complete fetch from all sources.

        1. Fetches from primary channel
        2. Runs all search queries
        3. Deduplicates and classifies
        4. Stores results in database

        Returns:
            FetchSummary with statistics
        """
        summary = FetchSummary()
        self._seen_ids.clear()

        # Fetch from primary channel first
        logger.info(f"Fetching from primary channel: {PRIMARY_CHANNEL['name']}")
        channel_videos = self._fetch_channel(PRIMARY_CHANNEL["url"])
        summary.total_videos_found += len(channel_videos)

        # Process channel videos
        channel_results = self._process_videos(
            channel_videos, f"channel:{PRIMARY_CHANNEL['name']}"
        )
        summary.new_videos_added += channel_results["added"]
        summary.music_excluded += channel_results["music_excluded"]
        summary.low_confidence_excluded += channel_results.get("low_confidence_excluded", 0)
        summary.unknown_channel_rejected += channel_results.get("unknown_channel_rejected", 0)

        # Run search queries
        for query in SEARCH_QUERIES:
            logger.info(f"Searching: '{query}'...")
            try:
                search_videos = self._fetch_search(query)
                new_count = len([v for v in search_videos if v.video_id not in self._seen_ids])
                dup_count = len(search_videos) - new_count

                summary.total_videos_found += new_count
                summary.duplicates_removed += dup_count

                # Process search results
                results = self._process_videos(search_videos, query)
                summary.new_videos_added += results["added"]
                summary.music_excluded += results["music_excluded"]
                summary.low_confidence_excluded += results.get("low_confidence_excluded", 0)
                summary.unknown_channel_rejected += results.get("unknown_channel_rejected", 0)

                if results["errors"]:
                    summary.errors.extend(results["errors"])

                # Enhanced logging with new filter counts
                excluded_count = (
                    results["music_excluded"] +
                    results.get("low_confidence_excluded", 0) +
                    results.get("unknown_channel_rejected", 0)
                )
                logger.info(
                    f"  Found {len(search_videos)} videos, "
                    f"{new_count} new, {dup_count} duplicates, "
                    f"{excluded_count} excluded, "
                    f"{results['added']} added"
                )

                # Rate limiting
                time.sleep(self.config["request_delay"])

            except Exception as e:
                error_msg = f"Error searching '{query}': {str(e)}"
                logger.error(error_msg)
                summary.errors.append(error_msg)

        # Get final statistics
        summary.total_in_database = self.db.get_video_count()
        summary.videos_needing_review = self.db.get_review_count()
        summary.unique_channels = self.db.get_unique_channels_count()
        summary.total_preaching_hours = self.db.get_total_preaching_hours()
        summary.top_channels = self.db.get_channel_breakdown()[:5]

        oldest, newest = self.db.get_date_range()
        summary.oldest_video_date = self._format_date(oldest)
        summary.newest_video_date = self._format_date(newest)

        return summary

    def _fetch_channel(self, channel_url: str) -> List[VideoMetadata]:
        """
        Fetch all videos from a YouTube channel.

        Args:
            channel_url: URL to the channel

        Returns:
            List of VideoMetadata objects
        """
        videos = []
        opts = self._ydl_opts.copy()
        opts["extract_flat"] = "in_playlist"  # Get playlist entries
        opts["playlistend"] = MAX_RESULTS_PER_QUERY

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Get channel videos tab
                videos_url = f"{channel_url}/videos"
                result = ydl.extract_info(videos_url, download=False)

                if result and "entries" in result:
                    entries = list(result["entries"])
                    logger.info(f"  Found {len(entries)} videos in channel")

                    for entry in entries:
                        if entry is None:
                            continue

                        video_id = entry.get("id")
                        if not video_id:
                            continue

                        # Get full video info
                        video = self._get_video_details(video_id)
                        if video:
                            video.search_query_used = f"channel:{channel_url}"
                            videos.append(video)
                            self._seen_ids.add(video_id)

                        time.sleep(0.5)  # Rate limit

        except Exception as e:
            logger.error(f"Error fetching channel {channel_url}: {e}")

        return videos

    def _fetch_search(self, query: str) -> List[VideoMetadata]:
        """
        Search YouTube for videos matching query.

        Args:
            query: Search query string

        Returns:
            List of VideoMetadata objects
        """
        videos = []
        opts = self._ydl_opts.copy()

        try:
            search_url = f"ytsearch{MAX_RESULTS_PER_QUERY}:{query}"

            with yt_dlp.YoutubeDL(opts) as ydl:
                result = ydl.extract_info(search_url, download=False)

                if result and "entries" in result:
                    for entry in result.get("entries", []):
                        if entry is None:
                            continue

                        video = VideoMetadata.from_ytdlp(entry, query)
                        if video.video_id:
                            videos.append(video)
                            self._seen_ids.add(video.video_id)

        except Exception as e:
            logger.error(f"Error searching '{query}': {e}")

        return videos

    def _get_video_details(self, video_id: str) -> Optional[VideoMetadata]:
        """
        Get full details for a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            VideoMetadata or None if error
        """
        opts = self._ydl_opts.copy()
        opts["extract_flat"] = False

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=False)
                if info:
                    return VideoMetadata.from_ytdlp(info)
        except Exception as e:
            logger.debug(f"Error getting details for {video_id}: {e}")

        return None

    def _process_videos(
        self, videos: List[VideoMetadata], source: str
    ) -> Dict:
        """
        Process, classify, and store videos with strict filtering.

        Applies multi-layer filtering:
        1. Skip duplicates
        2. Classify video (identity check, face verification, keywords, etc.)
        3. Apply storage thresholds (min confidence, music exclusion)
        4. Store only videos that pass all filters

        Args:
            videos: List of VideoMetadata to process
            source: Source identifier for logging

        Returns:
            Dictionary with processing results
        """
        results = {
            "added": 0,
            "skipped": 0,
            "music_excluded": 0,
            "low_confidence_excluded": 0,
            "unknown_channel_rejected": 0,
            "errors": [],
        }

        # Get storage thresholds
        min_storage_confidence = STORAGE_CONFIG.get("min_storage_confidence", 0.50)

        for video in videos:
            try:
                # Skip if already in database
                if self.db.video_exists(video.video_id):
                    results["skipped"] += 1
                    continue

                # Classify the video (applies identity check, face verification, etc.)
                video = self.classifier.classify(video)

                # --- STRICTER MUSIC FILTER ---
                # Exclude music with confidence > 0.50 (lowered from 0.70)
                if video.content_type == ContentType.MUSIC and video.confidence_score > 0.50:
                    results["music_excluded"] += 1
                    logger.debug(f"Music excluded: {video.video_id} (confidence: {video.confidence_score:.2f})")
                    continue

                # --- LOW CONFIDENCE FILTER ---
                # Skip UNKNOWN videos with very low confidence
                if video.content_type == ContentType.UNKNOWN:
                    if video.confidence_score < min_storage_confidence:
                        results["low_confidence_excluded"] += 1
                        logger.debug(
                            f"Low confidence excluded: {video.video_id} "
                            f"(type: {video.content_type.value}, confidence: {video.confidence_score:.2f})"
                        )
                        continue

                # --- UNKNOWN CHANNEL WITHOUT IDENTITY FILTER ---
                # Already handled in classifier, but double-check here
                if hasattr(video, 'channel_trust_level') and video.channel_trust_level == 0:
                    if hasattr(video, 'identity_matched') and not video.identity_matched:
                        if not video.face_verified:
                            results["unknown_channel_rejected"] += 1
                            logger.debug(
                                f"Unknown channel rejected: {video.video_id} "
                                f"(channel: {video.channel_name})"
                            )
                            continue

                # Store in database
                if self.db.insert_video(video):
                    results["added"] += 1
                    logger.debug(
                        f"Added: {video.video_id} "
                        f"(type: {video.content_type.value}, confidence: {video.confidence_score:.2f})"
                    )
                else:
                    results["skipped"] += 1

            except Exception as e:
                error_msg = f"Error processing video {video.video_id}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        # Log the fetch
        log = FetchLog(
            query_used=source,
            videos_found=len(videos),
            videos_added=results["added"],
            videos_skipped=results["skipped"],
            music_excluded=results["music_excluded"],
            errors_count=len(results["errors"]),
            error_messages="; ".join(results["errors"][:5]) if results["errors"] else None,
        )
        self.db.log_fetch(log)

        return results

    def _format_date(self, date_str: Optional[str]) -> Optional[str]:
        """Format YYYYMMDD to YYYY-MM-DD."""
        if date_str and len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        return date_str

    def fetch_single_video(self, video_url: str) -> Optional[VideoMetadata]:
        """
        Fetch and classify a single video by URL.

        Args:
            video_url: Full YouTube video URL

        Returns:
            Classified VideoMetadata or None
        """
        opts = self._ydl_opts.copy()

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if info:
                    video = VideoMetadata.from_ytdlp(info)
                    video = self.classifier.classify(video)
                    return video
        except Exception as e:
            logger.error(f"Error fetching {video_url}: {e}")

        return None


def run_fetch(db_path: Optional[str] = None) -> FetchSummary:
    """
    Convenience function to run a complete fetch.

    Args:
        db_path: Optional database path

    Returns:
        FetchSummary with results
    """
    db = Database(db_path) if db_path else Database()
    fetcher = VideoFetcher(db)
    return fetcher.fetch_all()
