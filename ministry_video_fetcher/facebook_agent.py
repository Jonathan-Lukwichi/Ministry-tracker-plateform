"""
Facebook Video Discovery Agent

Automated agent that searches Facebook for preacher videos using browser automation.
Uses Playwright to search Facebook Watch, extract video URLs, and verify with face recognition.

Usage:
    from facebook_agent import FacebookVideoAgent

    agent = FacebookVideoAgent(preacher_id=1)
    results = agent.discover_videos(queries=["Narcisse Majila preaching"])
"""

import os
import re
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")

from models import VideoMetadata, FetchSummary, ContentType, Preacher
from classifier import ContentClassifier, get_classifier_for_preacher
from database import Database
from config import (
    FACEBOOK_FETCHER_CONFIG,
    PLATFORM_FACEBOOK,
    STORAGE_CONFIG,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

AGENT_CONFIG = {
    # Browser settings
    "headless": True,  # Run browser in background
    "slow_mo": 100,  # Slow down actions (ms) for stability
    "timeout": 30000,  # Page load timeout (ms)

    # Search settings
    "max_scroll_iterations": 10,  # How many times to scroll for more results
    "scroll_delay": 2.0,  # Delay between scrolls (seconds)
    "max_videos_per_search": 50,  # Max videos to extract per search query

    # Rate limiting
    "delay_between_videos": 1.5,  # Delay between processing videos
    "delay_between_searches": 5.0,  # Delay between search queries

    # Paths
    "cookies_file": os.path.join(os.path.dirname(__file__), "facebook_cookies.txt"),
    "state_file": os.path.join(os.path.dirname(__file__), "browser_state.json"),
    "discovered_channels_file": os.path.join(os.path.dirname(__file__), "discovered_channels.json"),
}


# =============================================================================
# FACEBOOK VIDEO AGENT
# =============================================================================

class FacebookVideoAgent:
    """
    Automated agent for discovering preacher videos on Facebook.

    Uses Playwright browser automation to:
    1. Search Facebook Watch for preacher videos
    2. Extract video URLs from search results
    3. Verify preacher's presence using face recognition
    4. Store verified videos and learn new channels
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        preacher_id: Optional[int] = None,
        preacher: Optional[Preacher] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize the Facebook Video Agent.

        Args:
            db: Database instance
            preacher_id: ID of the preacher to search for
            preacher: Preacher object (alternative to preacher_id)
            config: Optional config override
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for the Facebook Agent. "
                "Install with: pip install playwright && playwright install chromium"
            )

        self.db = db or Database()
        self.preacher_id = preacher_id
        self.preacher = preacher
        self.config = {**AGENT_CONFIG, **(config or {})}

        # Load preacher from database if only ID provided
        if preacher_id and not preacher:
            preacher_data = self.db.get_preacher(preacher_id)
            if preacher_data:
                self.preacher = Preacher.from_dict(preacher_data)

        # Initialize classifier for face recognition
        if self.preacher_id:
            self.classifier = get_classifier_for_preacher(self.preacher_id)
        else:
            self.classifier = ContentClassifier()

        # Track seen video IDs
        self._seen_ids: Set[str] = set()

        # Browser instances
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        # yt-dlp options
        self._ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "extract_flat": False,
            "skip_download": True,
        }

        # Add cookies if available
        cookies_file = self.config.get("cookies_file")
        if cookies_file and os.path.exists(cookies_file):
            self._ydl_opts["cookiefile"] = cookies_file

    def _add_discovered_channel(self, channel_id: str, channel_name: str, channel_url: Optional[str] = None) -> None:
        """
        Add or update a discovered channel in the database.

        Args:
            channel_id: Facebook page/channel ID
            channel_name: Display name of the channel
            channel_url: Full URL to the channel (optional)
        """
        if not channel_url:
            channel_url = f"https://www.facebook.com/{channel_id}/videos"

        # Check if channel already exists
        existing = self.db.get_discovered_channel_by_url(channel_url)

        if not existing:
            # Add new channel
            self.db.add_discovered_channel(
                channel_name=channel_name,
                channel_url=channel_url,
                platform=PLATFORM_FACEBOOK,
                page_id=channel_id,
                preacher_id=self.preacher_id
            )
            logger.info(f"Discovered new channel: {channel_name} ({channel_id})")
        else:
            # Increment video count for existing channel
            self.db.increment_channel_video_count(channel_url)
            logger.debug(f"Updated channel: {channel_name}")

    def get_discovered_channels(self) -> List[Dict]:
        """Get list of discovered channels from database sorted by video count."""
        channels = self.db.get_all_discovered_channels(
            platform=PLATFORM_FACEBOOK,
            preacher_id=self.preacher_id
        )

        # Format for display
        result = []
        for ch in channels:
            result.append({
                "channel_id": ch.get("page_id"),
                "name": ch.get("channel_name"),
                "url": ch.get("channel_url"),
                "video_count": ch.get("video_count", 0),
                "first_seen": ch.get("discovered_at"),
                "last_scanned": ch.get("last_scanned"),
            })
        return result

    # =========================================================================
    # BROWSER MANAGEMENT
    # =========================================================================

    def _start_browser(self) -> None:
        """Start the Playwright browser with Facebook cookies."""
        if self._browser:
            return

        logger.info("Starting browser...")

        playwright = sync_playwright().start()

        self._browser = playwright.chromium.launch(
            headless=self.config.get("headless", True),
            slow_mo=self.config.get("slow_mo", 100),
        )

        # Create context with cookies
        self._context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Load cookies from file
        self._load_cookies_to_browser()

        self._page = self._context.new_page()
        self._page.set_default_timeout(self.config.get("timeout", 30000))

        logger.info("Browser started successfully")

    def _load_cookies_to_browser(self) -> None:
        """Load cookies from Netscape format file to browser context."""
        cookies_file = self.config.get("cookies_file")
        if not cookies_file or not os.path.exists(cookies_file):
            logger.warning("No cookies file found. Facebook access may be limited.")
            return

        try:
            cookies = []
            with open(cookies_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = line.split('\t')
                    if len(parts) >= 7:
                        domain, _, path, secure, expires, name, value = parts[:7]

                        cookie = {
                            "name": name,
                            "value": value,
                            "domain": domain,
                            "path": path,
                            "secure": secure.upper() == "TRUE",
                            "httpOnly": False,
                        }

                        # Add expiry if not session cookie
                        if expires and expires != "0":
                            try:
                                cookie["expires"] = int(expires)
                            except ValueError:
                                pass

                        cookies.append(cookie)

            if cookies:
                self._context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies to browser")

        except Exception as e:
            logger.error(f"Error loading cookies: {e}")

    def _stop_browser(self) -> None:
        """Stop the browser."""
        if self._page:
            self._page.close()
            self._page = None
        if self._context:
            self._context.close()
            self._context = None
        if self._browser:
            self._browser.close()
            self._browser = None
        logger.info("Browser stopped")

    # =========================================================================
    # FACEBOOK SEARCH
    # =========================================================================

    def _search_facebook_watch(self, query: str) -> List[str]:
        """
        Search Facebook Watch for videos matching the query.

        Args:
            query: Search query string

        Returns:
            List of video URLs found
        """
        video_urls = []

        try:
            # Navigate to Facebook Watch search
            search_url = f"https://www.facebook.com/watch/search/?q={query.replace(' ', '%20')}"
            logger.info(f"Searching: {search_url}")

            self._page.goto(search_url, wait_until="domcontentloaded")
            time.sleep(2)  # Wait for initial load

            # Check if we're logged in
            if "login" in self._page.url.lower():
                logger.warning("Not logged in to Facebook. Results may be limited.")

            # Scroll to load more videos
            max_scrolls = self.config.get("max_scroll_iterations", 10)
            scroll_delay = self.config.get("scroll_delay", 2.0)
            max_videos = self.config.get("max_videos_per_search", 50)

            for i in range(max_scrolls):
                # Extract video URLs from current page
                new_urls = self._extract_video_urls_from_page()

                for url in new_urls:
                    if url not in video_urls:
                        video_urls.append(url)

                logger.debug(f"Scroll {i+1}: Found {len(video_urls)} videos so far")

                # Stop if we have enough videos
                if len(video_urls) >= max_videos:
                    break

                # Scroll down
                self._page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(scroll_delay)

                # Check if we've reached the end
                new_height = self._page.evaluate("document.body.scrollHeight")
                if i > 0:
                    prev_height = self._page.evaluate("document.body.scrollHeight")
                    if new_height == prev_height:
                        logger.debug("Reached end of results")
                        break

            logger.info(f"Found {len(video_urls)} video URLs for query: '{query}'")

        except Exception as e:
            logger.error(f"Error searching Facebook: {e}")

        return video_urls[:self.config.get("max_videos_per_search", 50)]

    def _extract_video_urls_from_page(self) -> List[str]:
        """Extract video URLs from the current page."""
        video_urls = []

        try:
            # Find all video links on the page
            # Facebook video URLs typically contain /watch?v= or /videos/
            links = self._page.evaluate("""
                () => {
                    const urls = [];
                    const links = document.querySelectorAll('a[href*="/watch"], a[href*="/videos/"], a[href*="fb.watch"]');
                    links.forEach(link => {
                        const href = link.href;
                        if (href && !urls.includes(href)) {
                            urls.push(href);
                        }
                    });
                    return urls;
                }
            """)

            # Filter and clean URLs
            for url in links:
                cleaned = self._clean_video_url(url)
                if cleaned and cleaned not in video_urls:
                    video_urls.append(cleaned)

            # Also try to find video IDs in data attributes
            video_ids = self._page.evaluate("""
                () => {
                    const ids = [];
                    // Look for video elements with data attributes
                    document.querySelectorAll('[data-video-id], [data-ft*="video_id"]').forEach(el => {
                        const id = el.getAttribute('data-video-id') ||
                                   (el.getAttribute('data-ft') && JSON.parse(el.getAttribute('data-ft')).video_id);
                        if (id && !ids.includes(id)) {
                            ids.push(id);
                        }
                    });
                    return ids;
                }
            """)

            for vid_id in video_ids:
                url = f"https://www.facebook.com/watch?v={vid_id}"
                if url not in video_urls:
                    video_urls.append(url)

        except Exception as e:
            logger.debug(f"Error extracting video URLs: {e}")

        return video_urls

    def _clean_video_url(self, url: str) -> Optional[str]:
        """Clean and validate a Facebook video URL."""
        if not url:
            return None

        # Extract video ID from various URL formats
        patterns = [
            r'facebook\.com/watch\?v=(\d+)',
            r'facebook\.com/[^/]+/videos/(\d+)',
            r'facebook\.com/video\.php\?v=(\d+)',
            r'fb\.watch/([a-zA-Z0-9]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return f"https://www.facebook.com/watch?v={video_id}"

        # If URL contains /watch or /videos, return as-is
        if '/watch' in url or '/videos/' in url:
            return url

        return None

    # =========================================================================
    # VIDEO PROCESSING
    # =========================================================================

    def _fetch_video_metadata(self, video_url: str) -> Optional[VideoMetadata]:
        """
        Fetch video metadata using yt-dlp.

        Args:
            video_url: Facebook video URL

        Returns:
            VideoMetadata or None if fetch fails
        """
        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                if info:
                    video = VideoMetadata.from_ytdlp(
                        info,
                        f"fb_agent:{video_url}",
                        preacher_id=self.preacher_id
                    )
                    video.platform = PLATFORM_FACEBOOK

                    # Prefix video ID with fb_ to avoid conflicts
                    if not video.video_id.startswith("fb_"):
                        video.video_id = f"fb_{video.video_id}"

                    return video

        except Exception as e:
            logger.debug(f"Error fetching video {video_url}: {e}")

        return None

    def _verify_and_store_video(self, video: VideoMetadata) -> Tuple[bool, str]:
        """
        Verify video with face recognition and store if valid.

        Args:
            video: VideoMetadata to verify

        Returns:
            Tuple of (success, reason)
        """
        # Skip if already in database
        if self.db.video_exists(video.video_id):
            return False, "duplicate"

        # Skip if already seen this session
        if video.video_id in self._seen_ids:
            return False, "seen"

        self._seen_ids.add(video.video_id)

        # Classify video (includes face recognition)
        video = self.classifier.classify(video)

        # Log face verification result
        if video.face_verified:
            logger.info(f"✓ Face VERIFIED: {video.title[:50]}...")
        else:
            logger.debug(f"✗ Face not verified: {video.title[:50]}...")

        # Apply filters
        if video.content_type == ContentType.MUSIC and video.confidence_score > 0.50:
            return False, "music"

        if video.content_type == ContentType.UNKNOWN:
            # For agent discovery, we're stricter - require face verification
            if not video.face_verified and video.confidence_score < 0.60:
                return False, "low_confidence"

        # For agent discovery, prefer face-verified videos
        min_confidence = STORAGE_CONFIG.get("min_storage_confidence", 0.50)
        if not video.face_verified and video.confidence_score < min_confidence:
            return False, "no_face_match"

        # Store in database
        if self.db.insert_video(video):
            # Track the channel
            if video.channel_id and video.channel_name:
                self._add_discovered_channel(video.channel_id, video.channel_name)

            return True, "added"

        return False, "db_error"

    # =========================================================================
    # MAIN DISCOVERY METHODS
    # =========================================================================

    def discover_videos(
        self,
        queries: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> FetchSummary:
        """
        Discover videos by searching Facebook.

        Args:
            queries: List of search queries (default: uses preacher's search queries)
            limit: Maximum total videos to process

        Returns:
            FetchSummary with statistics
        """
        summary = FetchSummary()
        self._seen_ids.clear()

        # Get search queries
        if queries is None:
            if self.preacher:
                queries = self.preacher.get_search_queries(platform="facebook")
            else:
                queries = [
                    "Narcisse Majila preaching",
                    "Apostle Narcisse Majila",
                    "Narcisse Majila sermon",
                ]

        preacher_name = self.preacher.name if self.preacher else "Unknown"
        logger.info(f"Starting Facebook video discovery for: {preacher_name}")
        logger.info(f"Search queries: {queries}")

        try:
            # Start browser
            self._start_browser()

            total_processed = 0
            max_videos = limit or self.config.get("max_videos_per_search", 50) * len(queries)

            # Search for each query
            for query in queries:
                if total_processed >= max_videos:
                    break

                logger.info(f"\n--- Searching: '{query}' ---")

                # Search Facebook Watch
                video_urls = self._search_facebook_watch(query)
                logger.info(f"Found {len(video_urls)} video URLs")

                # Process each video
                for url in video_urls:
                    if total_processed >= max_videos:
                        break

                    try:
                        logger.debug(f"Processing: {url}")

                        # Fetch metadata
                        video = self._fetch_video_metadata(url)
                        if not video:
                            continue

                        summary.total_videos_found += 1

                        # Verify and store
                        success, reason = self._verify_and_store_video(video)

                        if success:
                            summary.new_videos_added += 1
                            logger.info(
                                f"✓ Added: {video.title[:50]}... "
                                f"(face_verified: {video.face_verified})"
                            )
                        elif reason == "duplicate" or reason == "seen":
                            summary.duplicates_removed += 1
                        elif reason == "music":
                            summary.music_excluded += 1
                        elif reason in ("low_confidence", "no_face_match"):
                            summary.low_confidence_excluded += 1

                        total_processed += 1

                        # Rate limiting
                        time.sleep(self.config.get("delay_between_videos", 1.5))

                    except Exception as e:
                        error_msg = f"Error processing {url}: {e}"
                        logger.debug(error_msg)
                        summary.errors.append(error_msg)

                # Delay between searches
                time.sleep(self.config.get("delay_between_searches", 5.0))

        finally:
            # Always stop browser
            self._stop_browser()

        # Get final statistics
        summary.total_in_database = self.db.get_video_count()
        summary.videos_needing_review = self.db.get_review_count()
        summary.unique_channels = self.db.get_unique_channels_count()
        summary.total_preaching_hours = self.db.get_total_preaching_hours()
        summary.top_channels = self.db.get_channel_breakdown()[:5]

        oldest, newest = self.db.get_date_range()
        if oldest:
            summary.oldest_video_date = f"{oldest[:4]}-{oldest[4:6]}-{oldest[6:]}" if len(oldest) == 8 else oldest
        if newest:
            summary.newest_video_date = f"{newest[:4]}-{newest[4:6]}-{newest[6:]}" if len(newest) == 8 else newest

        # Get discovered channels count from database
        discovered_channels = self.get_discovered_channels()

        logger.info(f"\nDiscovery complete:")
        logger.info(f"  Videos found: {summary.total_videos_found}")
        logger.info(f"  Videos added: {summary.new_videos_added}")
        logger.info(f"  Duplicates: {summary.duplicates_removed}")
        logger.info(f"  Excluded: {summary.music_excluded + summary.low_confidence_excluded}")
        logger.info(f"  Discovered channels: {len(discovered_channels)}")

        return summary

    def scan_discovered_channels(self, limit: Optional[int] = None) -> FetchSummary:
        """
        Scan previously discovered channels for new videos.

        This method re-visits channels where the preacher has been found before
        to discover new videos that may have been uploaded.

        Args:
            limit: Maximum videos to process

        Returns:
            FetchSummary with statistics
        """
        summary = FetchSummary()
        self._seen_ids.clear()

        channels = self.get_discovered_channels()
        if not channels:
            logger.info("No discovered channels to scan. Run discover_videos first.")
            return summary

        logger.info(f"Scanning {len(channels)} discovered channels...")

        try:
            self._start_browser()

            total_processed = 0
            max_videos = limit or 100

            for channel in channels:
                if total_processed >= max_videos:
                    break

                channel_id = channel.get("channel_id")
                channel_name = channel.get("name", "Unknown")

                logger.info(f"\n--- Scanning channel: {channel_name} ---")

                try:
                    # Navigate to channel videos
                    channel_url = f"https://www.facebook.com/{channel_id}/videos"
                    self._page.goto(channel_url, wait_until="networkidle")
                    time.sleep(2)

                    # Extract video URLs
                    video_urls = self._extract_video_urls_from_page()
                    logger.info(f"Found {len(video_urls)} videos on channel")

                    # Process videos
                    for url in video_urls[:20]:  # Limit per channel
                        if total_processed >= max_videos:
                            break

                        video = self._fetch_video_metadata(url)
                        if not video:
                            continue

                        summary.total_videos_found += 1

                        success, reason = self._verify_and_store_video(video)

                        if success:
                            summary.new_videos_added += 1
                            logger.info(f"✓ Added: {video.title[:50]}...")
                        elif reason == "duplicate":
                            summary.duplicates_removed += 1

                        total_processed += 1
                        time.sleep(self.config.get("delay_between_videos", 1.5))

                except Exception as e:
                    logger.error(f"Error scanning channel {channel_name}: {e}")
                    summary.errors.append(f"Channel {channel_name}: {e}")

                time.sleep(self.config.get("delay_between_searches", 5.0))

        finally:
            self._stop_browser()

        # Get final statistics
        summary.total_in_database = self.db.get_video_count()
        summary.total_preaching_hours = self.db.get_total_preaching_hours()

        return summary

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_browser()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def run_facebook_agent(
    queries: Optional[List[str]] = None,
    preacher_id: Optional[int] = None,
    limit: Optional[int] = None,
    headless: bool = True
) -> FetchSummary:
    """
    Run the Facebook Video Agent.

    Args:
        queries: Search queries (default: preacher's queries)
        preacher_id: Preacher ID to search for
        limit: Maximum videos to process
        headless: Run browser in background

    Returns:
        FetchSummary with statistics
    """
    config = {"headless": headless}

    agent = FacebookVideoAgent(
        preacher_id=preacher_id,
        config=config
    )

    return agent.discover_videos(queries=queries, limit=limit)


def check_playwright_installed() -> bool:
    """Check if Playwright is properly installed."""
    if not PLAYWRIGHT_AVAILABLE:
        return False

    try:
        with sync_playwright() as p:
            # Try to find chromium
            browser = p.chromium.launch(headless=True)
            browser.close()
            return True
    except Exception as e:
        logger.error(f"Playwright check failed: {e}")
        return False
