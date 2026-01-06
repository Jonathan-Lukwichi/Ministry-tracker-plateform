"""
Video Fetcher for Ministry Video Fetcher

Uses yt-dlp to fetch video metadata from YouTube and Facebook.
Supports multi-preacher fetching with dynamic search queries.
"""

import time
from datetime import datetime
from typing import List, Optional, Dict, Set
import logging

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

from models import VideoMetadata, FetchLog, FetchSummary, ContentType, Preacher
from classifier import ContentClassifier, get_classifier_for_preacher
from database import Database
from config import (
    SEARCH_QUERIES,
    PRIMARY_CHANNEL,
    MAX_RESULTS_PER_QUERY,
    FETCHER_CONFIG,
    STORAGE_CONFIG,
    IDENTITY_MARKERS,
    FACEBOOK_PAGES,
    FACEBOOK_SEARCH_QUERIES,
    FACEBOOK_FETCHER_CONFIG,
    PLATFORM_YOUTUBE,
    PLATFORM_FACEBOOK,
    generate_search_queries,
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
    Supports multi-preacher fetching with dynamic search queries.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        preacher_id: Optional[int] = None,
        preacher: Optional[Preacher] = None
    ):
        """
        Initialize the fetcher.

        Args:
            db: Database instance. Creates new one if None.
            preacher_id: ID of the preacher for preacher-specific fetching
            preacher: Preacher object (alternative to preacher_id)
        """
        self.db = db or Database()
        self.preacher_id = preacher_id
        self.preacher = preacher
        self.config = FETCHER_CONFIG

        # Load preacher from database if only ID provided
        if preacher_id and not preacher:
            preacher_data = self.db.get_preacher(preacher_id)
            if preacher_data:
                self.preacher = Preacher.from_dict(preacher_data)

        # Create preacher-aware classifier
        if self.preacher_id:
            self.classifier = get_classifier_for_preacher(self.preacher_id)
        else:
            self.classifier = ContentClassifier()

        # Generate dynamic search queries if preacher is set
        self._youtube_queries: List[str] = []
        self._facebook_queries: List[str] = []
        if self.preacher:
            self._youtube_queries = self.preacher.get_search_queries(platform="youtube")
            self._facebook_queries = self.preacher.get_search_queries(platform="facebook")
        else:
            # Legacy hardcoded queries
            self._youtube_queries = SEARCH_QUERIES
            self._facebook_queries = FACEBOOK_SEARCH_QUERIES

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

        1. Fetches from primary channel (if not using preacher-specific mode)
        2. Runs all search queries (dynamic or legacy)
        3. Deduplicates and classifies
        4. Stores results in database

        Returns:
            FetchSummary with statistics
        """
        summary = FetchSummary()
        self._seen_ids.clear()

        preacher_name = self.preacher.name if self.preacher else "Legacy Mode"
        logger.info(f"Starting YouTube fetch for: {preacher_name}")

        # Fetch from primary channel (only in legacy mode)
        if not self.preacher_id:
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

        # Run search queries (dynamic or legacy)
        for query in self._youtube_queries:
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

                        video = VideoMetadata.from_ytdlp(
                            entry, query, preacher_id=self.preacher_id
                        )
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
                    return VideoMetadata.from_ytdlp(
                        info, preacher_id=self.preacher_id
                    )
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
            video_url: Full video URL (YouTube or Facebook)

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

    # =========================================================================
    # FACEBOOK FETCHING METHODS
    # =========================================================================

    def fetch_facebook(self) -> FetchSummary:
        """
        Run complete fetch from all Facebook sources.

        1. Fetches from configured Facebook pages (only in legacy mode)
        2. Runs Facebook search queries (dynamic or legacy)
        3. Uses face recognition to verify preacher's presence
        4. Stores results in database

        Returns:
            FetchSummary with statistics
        """
        summary = FetchSummary()
        self._seen_ids.clear()

        preacher_name = self.preacher.name if self.preacher else "Legacy Mode"
        logger.info(f"Starting Facebook fetch for: {preacher_name}")

        # Get Facebook-specific settings
        fb_config = FACEBOOK_FETCHER_CONFIG
        request_delay = fb_config.get("request_delay", 3.0)

        # Fetch from Facebook pages (only in legacy mode)
        if not self.preacher_id:
            for page in FACEBOOK_PAGES:
                logger.info(f"Fetching Facebook page: {page['name']}")
                try:
                    page_videos = self._fetch_facebook_page(page["url"])
                    summary.total_videos_found += len(page_videos)

                    # Process page videos
                    results = self._process_videos(
                        page_videos, f"facebook_page:{page['name']}"
                    )
                    summary.new_videos_added += results["added"]
                    summary.music_excluded += results["music_excluded"]
                    summary.low_confidence_excluded += results.get("low_confidence_excluded", 0)
                    summary.unknown_channel_rejected += results.get("unknown_channel_rejected", 0)

                    logger.info(
                        f"  Found {len(page_videos)} videos, "
                        f"{results['added']} added"
                    )

                    time.sleep(request_delay)

                except Exception as e:
                    error_msg = f"Error fetching Facebook page {page['name']}: {str(e)}"
                    logger.error(error_msg)
                    summary.errors.append(error_msg)

        # Run Facebook search queries (dynamic or legacy)
        for query in self._facebook_queries:
            logger.info(f"Searching Facebook: '{query}'...")
            try:
                search_videos = self._fetch_facebook_search(query)
                new_count = len([v for v in search_videos if v.video_id not in self._seen_ids])
                dup_count = len(search_videos) - new_count

                summary.total_videos_found += new_count
                summary.duplicates_removed += dup_count

                # Process search results
                results = self._process_videos(search_videos, f"facebook_search:{query}")
                summary.new_videos_added += results["added"]
                summary.music_excluded += results["music_excluded"]
                summary.low_confidence_excluded += results.get("low_confidence_excluded", 0)
                summary.unknown_channel_rejected += results.get("unknown_channel_rejected", 0)

                if results["errors"]:
                    summary.errors.extend(results["errors"])

                logger.info(
                    f"  Found {len(search_videos)} videos, "
                    f"{new_count} new, {dup_count} duplicates, "
                    f"{results['added']} added"
                )

                time.sleep(request_delay)

            except Exception as e:
                error_msg = f"Error searching Facebook '{query}': {str(e)}"
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

    def _fetch_facebook_page(self, page_url: str) -> List[VideoMetadata]:
        """
        Fetch all videos from a Facebook page.

        Args:
            page_url: URL to the Facebook page videos (e.g., facebook.com/page/videos)

        Returns:
            List of VideoMetadata objects
        """
        videos = []
        opts = self._ydl_opts.copy()

        # Facebook-specific options
        fb_config = FACEBOOK_FETCHER_CONFIG
        opts["extract_flat"] = "in_playlist"
        opts["playlistend"] = fb_config.get("max_results_per_query", 50)

        # Add cookies if configured
        if fb_config.get("cookies_file"):
            opts["cookiefile"] = fb_config["cookies_file"]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                result = ydl.extract_info(page_url, download=False)

                if result and "entries" in result:
                    entries = list(result["entries"]) if result["entries"] else []
                    logger.info(f"  Found {len(entries)} videos on Facebook page")

                    for entry in entries:
                        if entry is None:
                            continue

                        video_id = entry.get("id")
                        if not video_id:
                            continue

                        # Get full video info
                        video = self._get_facebook_video_details(video_id, entry)
                        if video:
                            video.search_query_used = f"facebook_page:{page_url}"
                            videos.append(video)
                            self._seen_ids.add(video_id)

                        time.sleep(1.0)  # Rate limit

        except Exception as e:
            logger.error(f"Error fetching Facebook page {page_url}: {e}")

        return videos

    def _fetch_facebook_search(self, query: str) -> List[VideoMetadata]:
        """
        Search Facebook for videos matching query.

        Uses multiple search strategies for better results:
        1. Facebook Watch search (recommended)
        2. Facebook video search URL
        3. Facebook page search for video content

        Note: Facebook requires authentication (cookies) for best results.
        Without cookies, results will be limited.

        Args:
            query: Search query string (supports English and French)

        Returns:
            List of VideoMetadata objects
        """
        videos = []
        opts = self._ydl_opts.copy()

        # Facebook-specific options
        fb_config = FACEBOOK_FETCHER_CONFIG
        cookies_file = fb_config.get("cookies_file")

        # Check for cookies file and warn if missing
        if cookies_file:
            import os
            if os.path.exists(cookies_file):
                opts["cookiefile"] = cookies_file
                logger.info(f"Using Facebook cookies from: {cookies_file}")
            else:
                logger.warning(
                    f"Facebook cookies file not found: {cookies_file}\n"
                    "  To enable Facebook search:\n"
                    "  1. Install 'Get cookies.txt LOCALLY' browser extension\n"
                    "  2. Log in to Facebook\n"
                    "  3. Export cookies to 'facebook_cookies.txt'\n"
                    "  4. Place file in ministry_video_fetcher directory"
                )

        # URL encode the query properly (handle French accents)
        import urllib.parse
        encoded_query = urllib.parse.quote(query, safe='')

        # List of search URLs to try (in order of preference)
        search_urls = [
            # Facebook Watch search (best for video content)
            f"https://www.facebook.com/watch/search/?q={encoded_query}",
            # Facebook video search
            f"https://www.facebook.com/search/videos?q={encoded_query}",
            # Alternative: search all with video filter
            f"https://www.facebook.com/search/posts?q={encoded_query}&filters=video",
        ]

        for search_url in search_urls:
            try:
                logger.debug(f"Trying Facebook search URL: {search_url}")

                with yt_dlp.YoutubeDL(opts) as ydl:
                    result = ydl.extract_info(search_url, download=False)

                    if result and "entries" in result:
                        entries = list(result.get("entries", []) or [])

                        for entry in entries:
                            if entry is None:
                                continue

                            video = VideoMetadata.from_ytdlp(
                                entry, f"facebook_search:{query}",
                                preacher_id=self.preacher_id
                            )
                            if video.video_id and video.video_id not in self._seen_ids:
                                # Set platform to facebook
                                video.platform = PLATFORM_FACEBOOK
                                videos.append(video)
                                self._seen_ids.add(video.video_id)

                        if videos:
                            logger.info(f"Found {len(videos)} videos from Facebook search: '{query}'")
                            break  # Found videos, no need to try other URLs

            except Exception as e:
                error_str = str(e).lower()
                # Check for specific auth-related errors
                if "login" in error_str or "cookie" in error_str or "auth" in error_str:
                    logger.warning(f"Facebook search requires authentication for '{query}'")
                elif "rate" in error_str or "limit" in error_str:
                    logger.warning(f"Facebook rate limit hit, waiting before retry...")
                    time.sleep(5.0)  # Extra delay on rate limit
                else:
                    logger.debug(f"Facebook search URL failed for '{query}': {e}")
                continue

        if not videos:
            logger.info(f"No videos found from Facebook search: '{query}' (this may require cookies)")

        return videos

    def _get_facebook_video_details(
        self, video_id: str, entry: Optional[Dict] = None
    ) -> Optional[VideoMetadata]:
        """
        Get full details for a specific Facebook video.

        Args:
            video_id: Facebook video ID
            entry: Optional pre-fetched entry data

        Returns:
            VideoMetadata or None if error
        """
        opts = self._ydl_opts.copy()
        opts["extract_flat"] = False

        # Add cookies if configured
        fb_config = FACEBOOK_FETCHER_CONFIG
        if fb_config.get("cookies_file"):
            opts["cookiefile"] = fb_config["cookies_file"]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Try to construct Facebook video URL
                url = f"https://www.facebook.com/watch?v={video_id}"

                # If we have entry data with a URL, use that instead
                if entry and entry.get("url"):
                    url = entry["url"]
                elif entry and entry.get("webpage_url"):
                    url = entry["webpage_url"]

                info = ydl.extract_info(url, download=False)
                if info:
                    return VideoMetadata.from_ytdlp(
                        info, preacher_id=self.preacher_id
                    )

        except Exception as e:
            logger.debug(f"Error getting Facebook video details for {video_id}: {e}")

        # If full fetch fails, try to create from entry data
        if entry:
            try:
                return VideoMetadata.from_ytdlp(
                    entry, preacher_id=self.preacher_id
                )
            except Exception:
                pass

        return None

    def fetch_facebook_video_url(self, video_url: str) -> Optional[VideoMetadata]:
        """
        Fetch a single Facebook video by its URL.

        This is more reliable than search as it directly accesses the video.
        Supports various Facebook URL formats:
        - https://www.facebook.com/watch?v=VIDEO_ID
        - https://www.facebook.com/PAGE/videos/VIDEO_ID
        - https://fb.watch/SHORT_CODE
        - https://www.facebook.com/reel/VIDEO_ID

        Args:
            video_url: Full Facebook video URL

        Returns:
            VideoMetadata or None if error
        """
        opts = self._ydl_opts.copy()

        # Add cookies if configured
        fb_config = FACEBOOK_FETCHER_CONFIG
        cookies_file = fb_config.get("cookies_file")
        if cookies_file:
            import os
            if os.path.exists(cookies_file):
                opts["cookiefile"] = cookies_file

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if info:
                    video = VideoMetadata.from_ytdlp(
                        info,
                        f"facebook_direct:{video_url}",
                        preacher_id=self.preacher_id
                    )
                    video.platform = PLATFORM_FACEBOOK

                    # Process through classifier (includes face recognition)
                    video = self.classifier.classify(video)

                    logger.info(
                        f"Fetched Facebook video: {video.video_id} "
                        f"(face_verified: {video.face_verified}, "
                        f"confidence: {video.confidence_score:.2f})"
                    )

                    return video

        except Exception as e:
            logger.error(f"Error fetching Facebook video {video_url}: {e}")

        return None

    def fetch_facebook_videos_from_urls(self, urls: List[str]) -> FetchSummary:
        """
        Fetch multiple Facebook videos from a list of URLs.

        This is the most reliable method for fetching specific known videos.
        Each video is processed through the classifier with face recognition.

        Args:
            urls: List of Facebook video URLs

        Returns:
            FetchSummary with statistics
        """
        summary = FetchSummary()

        logger.info(f"Fetching {len(urls)} Facebook videos from URLs...")

        for url in urls:
            try:
                # Check if already in database
                video = self.fetch_facebook_video_url(url)

                if video:
                    summary.total_videos_found += 1

                    if self.db.video_exists(video.video_id):
                        summary.duplicates_removed += 1
                        logger.info(f"Duplicate skipped: {video.video_id}")
                        continue

                    # Check content type
                    if video.content_type == ContentType.MUSIC and video.confidence_score > 0.50:
                        summary.music_excluded += 1
                        continue

                    # Store in database
                    if self.db.insert_video(video):
                        summary.new_videos_added += 1
                        logger.info(f"Added: {video.video_id} - {video.title[:50]}...")

                # Rate limiting
                time.sleep(FACEBOOK_FETCHER_CONFIG.get("request_delay", 3.0))

            except Exception as e:
                error_msg = f"Error processing URL {url}: {str(e)}"
                logger.error(error_msg)
                summary.errors.append(error_msg)

        # Get final statistics
        summary.total_in_database = self.db.get_video_count()
        summary.videos_needing_review = self.db.get_review_count()
        summary.unique_channels = self.db.get_unique_channels_count()
        summary.total_preaching_hours = self.db.get_total_preaching_hours()

        return summary

    def fetch_all_platforms(self) -> FetchSummary:
        """
        Run complete fetch from all platforms (YouTube and Facebook).

        Returns:
            Combined FetchSummary with statistics from all platforms
        """
        logger.info("=" * 60)
        logger.info("FETCHING FROM ALL PLATFORMS")
        logger.info("=" * 60)

        # Fetch from YouTube
        logger.info("\n--- YOUTUBE ---")
        youtube_summary = self.fetch_all()

        # Fetch from Facebook
        logger.info("\n--- FACEBOOK ---")
        facebook_summary = self.fetch_facebook()

        # Combine summaries
        combined = FetchSummary()
        combined.total_videos_found = youtube_summary.total_videos_found + facebook_summary.total_videos_found
        combined.duplicates_removed = youtube_summary.duplicates_removed + facebook_summary.duplicates_removed
        combined.music_excluded = youtube_summary.music_excluded + facebook_summary.music_excluded
        combined.low_confidence_excluded = youtube_summary.low_confidence_excluded + facebook_summary.low_confidence_excluded
        combined.unknown_channel_rejected = youtube_summary.unknown_channel_rejected + facebook_summary.unknown_channel_rejected
        combined.new_videos_added = youtube_summary.new_videos_added + facebook_summary.new_videos_added

        # Use latest database stats
        combined.total_in_database = facebook_summary.total_in_database
        combined.videos_needing_review = facebook_summary.videos_needing_review
        combined.unique_channels = facebook_summary.unique_channels
        combined.total_preaching_hours = facebook_summary.total_preaching_hours
        combined.top_channels = facebook_summary.top_channels
        combined.oldest_video_date = facebook_summary.oldest_video_date
        combined.newest_video_date = facebook_summary.newest_video_date
        combined.errors = youtube_summary.errors + facebook_summary.errors

        return combined


def run_fetch(db_path: Optional[str] = None) -> FetchSummary:
    """
    Convenience function to run a complete fetch (legacy mode).

    Args:
        db_path: Optional database path

    Returns:
        FetchSummary with results
    """
    db = Database(db_path) if db_path else Database()
    fetcher = VideoFetcher(db)
    return fetcher.fetch_all()


def run_fetch_for_preacher(
    preacher_id: int,
    platform: str = "youtube",
    db_path: Optional[str] = None
) -> FetchSummary:
    """
    Run a fetch for a specific preacher.

    Args:
        preacher_id: ID of the preacher to fetch for
        platform: 'youtube', 'facebook', or 'all'
        db_path: Optional database path

    Returns:
        FetchSummary with results
    """
    db = Database(db_path) if db_path else Database()
    fetcher = VideoFetcher(db, preacher_id=preacher_id)

    if platform == "youtube":
        return fetcher.fetch_all()
    elif platform == "facebook":
        return fetcher.fetch_facebook()
    elif platform == "all":
        return fetcher.fetch_all_platforms()
    else:
        raise ValueError(f"Invalid platform: {platform}")


def get_fetcher_for_preacher(preacher_id: int, db: Optional[Database] = None) -> VideoFetcher:
    """
    Get a VideoFetcher configured for a specific preacher.

    Args:
        preacher_id: ID of the preacher
        db: Optional Database instance

    Returns:
        VideoFetcher instance configured for the preacher
    """
    return VideoFetcher(db=db, preacher_id=preacher_id)
