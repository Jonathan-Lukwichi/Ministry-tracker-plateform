"""
Facebook Graph API Client for Ministry Video Fetcher.

Provides reliable video discovery using Facebook's official Graph API,
with fallback to yt-dlp for video URL extraction.

Usage:
    from facebook_api import FacebookGraphClient, TokenManager

    client = FacebookGraphClient()
    videos = client.get_page_videos("ramahfgpta")
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError("requests is required. Install with: pip install requests")

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class FacebookAPIError(Exception):
    """Base exception for Facebook API errors."""
    pass


class TokenExpiredError(FacebookAPIError):
    """Token needs refresh or replacement."""
    pass


class TokenInvalidError(FacebookAPIError):
    """Token is invalid or revoked."""
    pass


class RateLimitError(FacebookAPIError):
    """API rate limit exceeded."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class PermissionError(FacebookAPIError):
    """Missing required permissions."""
    def __init__(self, message: str, missing_permission: str = None):
        super().__init__(message)
        self.missing_permission = missing_permission


class PageNotFoundError(FacebookAPIError):
    """Facebook page not found."""
    pass


# =============================================================================
# TOKEN MANAGER
# =============================================================================

class TokenManager:
    """
    Manages Facebook API tokens with persistence and refresh.

    Tokens are stored in a JSON file with expiration tracking.
    Long-lived Page Access Tokens last approximately 60 days.
    """

    def __init__(self, token_file: str = None, config: dict = None):
        """
        Initialize token manager.

        Args:
            token_file: Path to token storage file
            config: Configuration dict with app credentials
        """
        self.config = config or {}
        self.token_file = token_file or self.config.get("token_file", "fb_token.json")

        # Resolve path relative to this module
        if not os.path.isabs(self.token_file):
            module_dir = os.path.dirname(os.path.abspath(__file__))
            self.token_file = os.path.join(module_dir, self.token_file)

        self._token_data = None
        self._load_token()

    def _load_token(self) -> None:
        """Load token from storage file."""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    self._token_data = json.load(f)
                logger.debug(f"Loaded token from {self.token_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load token file: {e}")
                self._token_data = None
        else:
            self._token_data = None

    def _save_token(self) -> None:
        """Save token to storage file."""
        if self._token_data:
            try:
                with open(self.token_file, 'w') as f:
                    json.dump(self._token_data, f, indent=2, default=str)
                logger.debug(f"Saved token to {self.token_file}")
            except IOError as e:
                logger.error(f"Could not save token file: {e}")

    def get_access_token(self) -> Optional[str]:
        """
        Get current access token.

        Returns:
            Access token string or None if not available
        """
        # Try from stored token data
        if self._token_data and self._token_data.get("access_token"):
            return self._token_data["access_token"]

        # Fall back to config
        return self.config.get("access_token")

    def save_token(
        self,
        token: str,
        expires_at: datetime = None,
        token_type: str = "page",
        page_id: str = None
    ) -> None:
        """
        Save a new token with metadata.

        Args:
            token: The access token string
            expires_at: Token expiration datetime (default: 60 days from now)
            token_type: Type of token (user, page, app)
            page_id: Associated page ID if applicable
        """
        if expires_at is None:
            # Default to 60 days for long-lived tokens
            expires_at = datetime.utcnow() + timedelta(days=60)

        self._token_data = {
            "access_token": token,
            "token_type": token_type,
            "expires_at": expires_at.isoformat(),
            "page_id": page_id,
            "app_id": self.config.get("app_id"),
            "saved_at": datetime.utcnow().isoformat(),
        }
        self._save_token()
        logger.info(f"Token saved. Expires at: {expires_at}")

    def is_token_valid(self) -> bool:
        """
        Check if current token exists and is not expired.

        Returns:
            True if token is valid, False otherwise
        """
        token = self.get_access_token()
        if not token:
            return False

        # Check expiration if available
        if self._token_data and self._token_data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(self._token_data["expires_at"])
                if datetime.utcnow() >= expires_at:
                    logger.warning("Token has expired")
                    return False
            except ValueError:
                pass

        return True

    def get_expiry(self) -> Optional[datetime]:
        """Get token expiration datetime."""
        if self._token_data and self._token_data.get("expires_at"):
            try:
                return datetime.fromisoformat(self._token_data["expires_at"])
            except ValueError:
                pass
        return None

    def days_until_expiry(self) -> Optional[int]:
        """Get number of days until token expires."""
        expiry = self.get_expiry()
        if expiry:
            delta = expiry - datetime.utcnow()
            return max(0, delta.days)
        return None

    def needs_refresh(self, days_before: int = 7) -> bool:
        """
        Check if token should be refreshed.

        Args:
            days_before: Refresh if expiring within this many days

        Returns:
            True if token should be refreshed
        """
        days = self.days_until_expiry()
        if days is None:
            return False
        return days <= days_before

    def get_token_info(self) -> dict:
        """Get information about the current token."""
        return {
            "has_token": bool(self.get_access_token()),
            "is_valid": self.is_token_valid(),
            "expires_at": self.get_expiry(),
            "days_until_expiry": self.days_until_expiry(),
            "needs_refresh": self.needs_refresh(),
            "token_type": self._token_data.get("token_type") if self._token_data else None,
            "page_id": self._token_data.get("page_id") if self._token_data else None,
        }


# =============================================================================
# FACEBOOK GRAPH API CLIENT
# =============================================================================

class FacebookGraphClient:
    """
    Facebook Graph API client for video discovery.

    Uses official Graph API endpoints to reliably discover videos
    from Facebook pages. Does not extract video URLs directly -
    use yt-dlp for that functionality.
    """

    # Default video fields to request
    DEFAULT_VIDEO_FIELDS = [
        "id",
        "title",
        "description",
        "created_time",
        "length",
        "permalink_url",
        "thumbnails",
        "from",
        "live_status",
    ]

    def __init__(self, config: dict = None):
        """
        Initialize Facebook Graph API client.

        Args:
            config: Configuration dict with API settings
        """
        self.config = config or {}
        self.api_version = self.config.get("api_version", "v18.0")
        self.base_url = self.config.get(
            "base_url",
            f"https://graph.facebook.com/{self.api_version}"
        )

        # Initialize token manager
        self.token_manager = TokenManager(config=self.config)

        # Rate limiting
        self.request_delay = self.config.get("request_delay", 0.5)
        self._last_request_time = 0

        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "MinistryVideoFetcher/1.0"
        })

    def _get_access_token(self) -> str:
        """Get access token, raising error if not available."""
        token = self.token_manager.get_access_token()
        if not token:
            raise TokenInvalidError(
                "No access token available. "
                "Run 'python main.py fb-token --set YOUR_TOKEN' to set one."
            )
        return token

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: dict = None,
        method: str = "GET"
    ) -> dict:
        """
        Make a request to the Graph API.

        Args:
            endpoint: API endpoint (e.g., "/me/videos")
            params: Query parameters
            method: HTTP method

        Returns:
            JSON response as dict

        Raises:
            FacebookAPIError: On API errors
        """
        self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params["access_token"] = self._get_access_token()

        try:
            if method == "GET":
                response = self._session.get(url, params=params, timeout=30)
            else:
                response = self._session.post(url, data=params, timeout=30)

            data = response.json()

            # Check for errors
            if "error" in data:
                error = data["error"]
                error_code = error.get("code")
                error_message = error.get("message", "Unknown error")

                # Token errors
                if error_code in (190, 102):
                    raise TokenExpiredError(f"Token error: {error_message}")

                # Rate limiting
                if error_code == 4 or "rate limit" in error_message.lower():
                    raise RateLimitError(error_message, retry_after=60)

                # Permission errors
                if error_code in (10, 200, 210):
                    raise PermissionError(error_message)

                # Not found
                if error_code == 803:
                    raise PageNotFoundError(error_message)

                raise FacebookAPIError(f"API Error {error_code}: {error_message}")

            return data

        except requests.RequestException as e:
            raise FacebookAPIError(f"Request failed: {e}")

    def validate_token(self) -> dict:
        """
        Validate the current access token.

        Returns:
            Token debug info from Facebook
        """
        try:
            data = self._make_request("/debug_token", {
                "input_token": self._get_access_token()
            })
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return {"is_valid": False, "error": str(e)}

    def get_page_info(self, page_id: str) -> dict:
        """
        Get information about a Facebook page.

        Args:
            page_id: Page ID or username

        Returns:
            Page information dict
        """
        return self._make_request(f"/{page_id}", {
            "fields": "id,name,about,fan_count,link"
        })

    def get_page_videos(
        self,
        page_id: str,
        limit: int = 50,
        fields: List[str] = None
    ) -> List[dict]:
        """
        Fetch videos from a Facebook page.

        Args:
            page_id: Page ID or username
            limit: Maximum number of videos to fetch
            fields: Video fields to request

        Returns:
            List of video data dicts
        """
        fields = fields or self.DEFAULT_VIDEO_FIELDS

        videos = []
        endpoint = f"/{page_id}/videos"
        params = {
            "fields": ",".join(fields),
            "limit": min(limit, 100)  # Max 100 per request
        }

        logger.info(f"Fetching videos from Facebook page: {page_id}")

        while len(videos) < limit:
            try:
                data = self._make_request(endpoint, params)

                page_videos = data.get("data", [])
                if not page_videos:
                    break

                videos.extend(page_videos)
                logger.debug(f"Fetched {len(page_videos)} videos (total: {len(videos)})")

                # Check for next page
                paging = data.get("paging", {})
                next_url = paging.get("next")

                if not next_url or len(videos) >= limit:
                    break

                # Extract cursor for next request
                cursors = paging.get("cursors", {})
                after = cursors.get("after")
                if not after:
                    break

                params["after"] = after

            except PageNotFoundError:
                logger.warning(f"Page not found: {page_id}")
                break
            except RateLimitError as e:
                logger.warning(f"Rate limited. Waiting {e.retry_after}s...")
                time.sleep(e.retry_after)
            except Exception as e:
                logger.error(f"Error fetching videos from {page_id}: {e}")
                break

        logger.info(f"Total videos fetched from {page_id}: {len(videos)}")
        return videos[:limit]

    def get_video_details(self, video_id: str) -> dict:
        """
        Get detailed information about a specific video.

        Args:
            video_id: Facebook video ID

        Returns:
            Video details dict
        """
        fields = self.DEFAULT_VIDEO_FIELDS + [
            "views",
            "reactions.summary(total_count)",
            "comments.summary(total_count)"
        ]

        return self._make_request(f"/{video_id}", {
            "fields": ",".join(fields)
        })

    def exchange_for_long_lived_token(
        self,
        short_lived_token: str = None
    ) -> dict:
        """
        Exchange a short-lived token for a long-lived token.

        Long-lived Page Access Tokens last approximately 60 days.

        Args:
            short_lived_token: Token to exchange (uses current if not provided)

        Returns:
            Dict with new token and expiry info
        """
        app_id = self.config.get("app_id")
        app_secret = self.config.get("app_secret")

        if not app_id or not app_secret:
            raise FacebookAPIError(
                "App ID and App Secret required for token exchange. "
                "Set them in FACEBOOK_GRAPH_API_CONFIG."
            )

        token = short_lived_token or self._get_access_token()

        data = self._make_request("/oauth/access_token", {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token
        })

        new_token = data.get("access_token")
        expires_in = data.get("expires_in", 5184000)  # Default 60 days

        if new_token:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            self.token_manager.save_token(new_token, expires_at)
            logger.info(f"Token exchanged. New token expires in {expires_in // 86400} days")

        return {
            "access_token": new_token,
            "expires_in": expires_in,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
        }

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_facebook_client(config: dict = None) -> FacebookGraphClient:
    """
    Get a configured Facebook Graph API client.

    Args:
        config: Optional config override

    Returns:
        Configured FacebookGraphClient instance
    """
    if config is None:
        try:
            from config import FACEBOOK_GRAPH_API_CONFIG
            config = FACEBOOK_GRAPH_API_CONFIG
        except ImportError:
            config = {}

    return FacebookGraphClient(config)


def check_token_status() -> dict:
    """
    Check the status of the current Facebook API token.

    Returns:
        Dict with token status information
    """
    try:
        from config import FACEBOOK_GRAPH_API_CONFIG
        config = FACEBOOK_GRAPH_API_CONFIG
    except ImportError:
        config = {}

    manager = TokenManager(config=config)
    return manager.get_token_info()
