"""
Content Classifier for Ministry Video Fetcher

Classifies videos as PREACHING, MUSIC, or UNKNOWN based on
title, description, duration analysis, and face recognition.

Supports preacher-specific classification with dynamic identity markers.
"""

import os
import re
from typing import Tuple, Optional, Dict, List

from models import VideoMetadata, ContentType, Language, Preacher
from config import (
    PREACHING_KEYWORDS_EN,
    PREACHING_KEYWORDS_FR,
    MUSIC_KEYWORDS,
    STRONG_MUSIC_INDICATORS,
    FRENCH_INDICATORS,
    ENGLISH_INDICATORS,
    CLASSIFICATION_CONFIG,
    FACE_RECOGNITION_CONFIG,
    STRICT_CHANNELS,
    TRUSTED_CHANNELS,
    IDENTITY_MARKERS,
    CHANNEL_TRUST_LEVELS,
    FACE_VERIFICATION_REQUIREMENTS,
    STORAGE_CONFIG,
    generate_identity_markers,
    get_photos_directory,
)

# Compute photos directory relative to project root
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_MODULE_DIR)
PHOTOS_DIR = os.path.join(_PROJECT_DIR, "photos")

# Import face recognition module
try:
    from face_recognition import get_face_recognizer, FaceResult
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: Face recognition module not available.")


class ContentClassifier:
    """
    Classifies video content as preaching or music.

    Uses keyword matching, duration analysis, and confidence scoring
    to determine content type and flag uncertain classifications.

    Supports preacher-specific classification with dynamic identity markers.
    """

    def __init__(
        self,
        use_frame_extraction: bool = True,
        preacher_id: Optional[int] = None,
        preacher: Optional[Preacher] = None
    ):
        """
        Initialize classifier with keyword sets and face recognition.

        Args:
            use_frame_extraction: Whether to extract video frames for face detection
            preacher_id: ID of the preacher for preacher-specific classification
            preacher: Preacher object (alternative to preacher_id)
        """
        # Store preacher info
        self.preacher_id = preacher_id
        self.preacher = preacher

        # --- Keyword setup ---
        self.preaching_keywords = set(kw.lower() for kw in PREACHING_KEYWORDS_EN + PREACHING_KEYWORDS_FR)
        self.music_keywords = set(kw.lower() for kw in MUSIC_KEYWORDS)
        self.strong_music = set(kw.lower() for kw in STRONG_MUSIC_INDICATORS)
        self.french_words = set(w.lower() for w in FRENCH_INDICATORS)
        self.english_words = set(w.lower() for w in ENGLISH_INDICATORS)
        self.config = CLASSIFICATION_CONFIG

        # --- Dynamic Identity Markers ---
        if preacher:
            # Generate identity markers from preacher data
            self.identity_markers = preacher.get_identity_markers()
        elif preacher_id:
            # Try to load preacher from database
            try:
                from database import Database
                db = Database()
                preacher_data = db.get_preacher(preacher_id)
                if preacher_data:
                    self.preacher = Preacher.from_dict(preacher_data)
                    self.identity_markers = self.preacher.get_identity_markers()
                else:
                    self.identity_markers = IDENTITY_MARKERS
            except Exception as e:
                print(f"Warning: Could not load preacher {preacher_id}: {e}")
                self.identity_markers = IDENTITY_MARKERS
        else:
            # Use legacy hardcoded identity markers
            self.identity_markers = IDENTITY_MARKERS

        # --- Face Recognition setup ---
        self.use_frame_extraction = use_frame_extraction
        self.face_recognizer = None
        self.strict_channels = set(ch.lower() for ch in STRICT_CHANNELS)
        self.trusted_channels = set(ch.lower() for ch in TRUSTED_CHANNELS)

        if FACE_RECOGNITION_AVAILABLE:
            try:
                # Use preacher-specific photos directory if preacher_id provided
                photos_dir = None
                if preacher_id:
                    photos_dir = get_photos_directory(preacher_id)
                else:
                    photos_dir = PHOTOS_DIR

                self.face_recognizer = get_face_recognizer(
                    preacher_id=preacher_id,
                    config=FACE_RECOGNITION_CONFIG,
                    photos_dir=photos_dir
                )
                print(f"Face recognition initialized with {len(self.face_recognizer.reference_image_paths)} reference images.")
            except Exception as e:
                print(f"Warning: Could not initialize face recognition: {e}")
                self.face_recognizer = None

    def _is_strict_channel(self, channel_name: str) -> bool:
        """Check if the video is from a strict channel requiring face verification."""
        if not channel_name:
            return False
        channel_lower = channel_name.lower()
        return any(strict in channel_lower or channel_lower in strict
                   for strict in self.strict_channels)

    def _is_trusted_channel(self, channel_name: str) -> bool:
        """Check if the video is from a trusted channel (skip face verification)."""
        if not channel_name:
            return False
        channel_lower = channel_name.lower()
        return any(trusted in channel_lower or channel_lower in trusted
                   for trusted in self.trusted_channels)

    def _check_identity_markers(self, text: str) -> Tuple[bool, float, bool]:
        """
        Check if video contains identity markers (preacher's name or church).

        Uses dynamic identity markers based on the configured preacher.

        Args:
            text: Combined title and description text (lowercase)

        Returns:
            Tuple of (has_identity, boost_score, has_name)
            - has_identity: True if name/church found (for backwards compat)
            - boost_score: 0.0-0.30 based on match strength
            - has_name: True ONLY if preacher's actual name found (not just church)
        """
        require_name = self.identity_markers.get("require_name_not_just_church", True)

        # Check for required names (strongest match)
        for name in self.identity_markers.get("required_names", []):
            if name in text:
                return True, 0.30, True  # has_identity, boost, has_name

        # Check acceptable names (good match)
        for name in self.identity_markers.get("acceptable_names", []):
            if name in text:
                return True, 0.25, True  # has_identity, boost, has_name

        # Check church names - NO LONGER counts as identity if require_name is True
        for church in self.identity_markers.get("church_names", []):
            if church in text:
                if require_name:
                    # Church name found but NOT the preacher's name
                    # Return small boost but has_identity=False, has_name=False
                    return False, 0.10, False
                else:
                    # Legacy behavior: church name counts as identity
                    return True, 0.15, False

        return False, 0.0, False

    def _get_channel_trust_level(self, channel_name: str) -> int:
        """
        Get trust level for a channel.

        Returns:
            3 = verified (auto-accept, skip all validation)
            2 = trusted (identity OR face required)
            1 = known (identity AND face required)
            0 = unknown (strictest validation)
        """
        if not channel_name:
            return 0

        channel_lower = channel_name.lower()

        # Check verified channels (level 3)
        for ch in CHANNEL_TRUST_LEVELS.get("verified", []):
            if ch.lower() in channel_lower or channel_lower in ch.lower():
                return 3

        # Check trusted channels (level 2)
        for ch in CHANNEL_TRUST_LEVELS.get("trusted", []):
            if ch.lower() in channel_lower or channel_lower in ch.lower():
                return 2

        # Check known channels (level 1)
        for ch in CHANNEL_TRUST_LEVELS.get("known", []):
            if ch.lower() in channel_lower or channel_lower in ch.lower():
                return 1

        return 0

    def _verify_face(self, video: VideoMetadata) -> Tuple[bool, float]:
        """
        Verify if the target person's face is in the video.

        Uses enhanced face recognition with optional frame extraction.
        NOTE: No longer auto-passes for trusted channels - must actually verify.

        Args:
            video: VideoMetadata to verify

        Returns:
            Tuple of (verified, confidence)
        """
        if not self.face_recognizer:
            return False, 0.0

        # REMOVED: Auto-pass for trusted channels
        # Trusted channels still need identity OR actual face verification

        try:
            # Use frame extraction for strict channels or if enabled
            use_frames = self.use_frame_extraction and (
                self._is_strict_channel(video.channel_name) or
                FACE_RECOGNITION_CONFIG.get("enable_frame_extraction", True)
            )

            result = self.face_recognizer.verify_face(
                video_url=video.video_url,
                thumbnail_url=video.thumbnail_url,
                use_frames=use_frames
            )

            if result.verified:
                print(f"Face verified for video: {video.video_id} (source: {result.source})")
                return True, result.confidence

            return False, result.confidence

        except Exception as e:
            print(f"Warning: Face verification failed for {video.video_id}: {e}")
            return False, 0.0

    def classify(self, video: VideoMetadata) -> VideoMetadata:
        """
        Classify a video and update its metadata.

        Uses multi-layer filtering:
        1. Identity validation (preacher's name or church in title/description)
        2. Channel trust levels
        3. Face verification
        4. Keyword matching
        5. Duration analysis

        Args:
            video: VideoMetadata to classify

        Returns:
            Updated VideoMetadata with content_type, confidence, and review flag
        """
        # Set preacher_id on video if classifier has one
        if self.preacher_id and not video.preacher_id:
            video.preacher_id = self.preacher_id

        # Get text to analyze
        text = self._get_searchable_text(video)

        # --- Check identity markers ---
        # Returns (has_identity, boost, has_name)
        # has_name = True ONLY if preacher's actual name found (not just church)
        has_identity, identity_boost, has_name = self._check_identity_markers(text)
        video.identity_matched = has_name  # Only True if preacher's name found

        # --- NEW: Get channel trust level ---
        channel_trust_level = self._get_channel_trust_level(video.channel_name)
        video.channel_trust_level = channel_trust_level

        # --- Face Verification Step ---
        face_verified, face_confidence = self._verify_face(video)
        video.face_verified = face_verified

        # Check if face meets minimum confidence threshold
        face_meets_threshold = face_confidence >= FACE_VERIFICATION_REQUIREMENTS.get("min_confidence", 0.70)
        if face_verified and not face_meets_threshold:
            # Face detection returned verified but with low confidence (OpenCV fallback)
            face_verified = False
            print(f"Face verification rejected for {video.video_id}: confidence {face_confidence:.2f} < threshold")

        # --- VERIFIED CHANNEL: Auto-accept ---
        if channel_trust_level == 3:
            video.content_type = ContentType.PREACHING
            video.confidence_score = 0.95
            video.needs_review = False
            video.language_detected = self._detect_language(text)
            return video

        # Check for strong music indicators first
        if self._has_strong_music_indicators(text) and not face_verified:
            video.content_type = ContentType.MUSIC
            video.confidence_score = 0.95
            video.needs_review = False
            video.language_detected = self._detect_language(text)
            return video

        # Count keyword matches
        preaching_score = self._count_preaching_keywords(text)
        music_score = self._count_music_keywords(text)

        # Get duration-based score
        duration_score = self._get_duration_score(video.duration)

        # --- STRICTER CHECK: Require preacher's NAME in title ---
        # For ALL channels (including trusted), require the preacher's actual name
        # This ensures we don't include videos of other preachers from same church
        # Church name alone is NOT enough
        if not has_name:
            # Check if face verification is available AND actually verified
            if not face_verified or face_confidence < 0.70:
                # No preacher name AND no verified face = reject
                video.content_type = ContentType.UNKNOWN
                video.confidence_score = 0.25
                video.needs_review = True
                video.language_detected = self._detect_language(text)
                print(f"Rejected - no preacher name: {video.video_id} - '{video.title[:60]}...'")
                return video

        # --- Check face verification requirements for unknown channels ---
        if channel_trust_level == 0:  # Unknown channel
            if FACE_VERIFICATION_REQUIREMENTS.get("required_for_unknown_channels", True):
                if not face_verified and not has_name:
                    # Unknown channel, no face, no identity = reject
                    video.content_type = ContentType.UNKNOWN
                    video.confidence_score = 0.20
                    video.needs_review = True
                    video.language_detected = self._detect_language(text)
                    print(f"Unknown channel rejected: {video.video_id} (no identity or face)")
                    return video

        # Calculate final classification with all factors
        content_type, confidence = self._calculate_classification(
            preaching_score=preaching_score,
            music_score=music_score,
            duration_score=duration_score,
            face_verified=face_verified,
            has_identity=has_name,  # Use has_name instead of has_identity
            identity_boost=identity_boost,
            channel_trust_level=channel_trust_level
        )

        # --- STRICT CHANNEL LOGIC ---
        # If from a strict channel and face not verified, flag for review
        is_strict = self._is_strict_channel(video.channel_name)
        if is_strict and not face_verified:
            if content_type == ContentType.PREACHING:
                # Downgrade to UNKNOWN for review
                content_type = ContentType.UNKNOWN
                confidence = 0.30
                print(f"Strict channel: Video {video.video_id} flagged for review (no face match)")
            video.needs_review = True
        else:
            # Use new review threshold from STORAGE_CONFIG
            review_threshold = STORAGE_CONFIG.get("review_threshold", 0.70)
            video.needs_review = confidence < review_threshold and not face_verified

        # Update video
        video.content_type = content_type
        video.confidence_score = confidence

        # Detect language
        video.language_detected = self._detect_language(text)

        return video

    def _get_searchable_text(self, video: VideoMetadata) -> str:
        """Combine title and description for keyword matching."""
        parts = []
        if video.title:
            parts.append(video.title)
        if video.description:
            parts.append(video.description)
        return " ".join(parts).lower()

    def _has_strong_music_indicators(self, text: str) -> bool:
        """Check if text contains strong music indicators."""
        for indicator in self.strong_music:
            if indicator in text:
                return True
        return False

    def _count_preaching_keywords(self, text: str) -> int:
        """Count number of preaching keywords found in text."""
        count = 0
        for keyword in self.preaching_keywords:
            if keyword in text:
                count += 1
                # Give extra weight to strong indicators
                if keyword in ["sermon", "preaching", "predication", "enseignement"]:
                    count += 1
        return count

    def _count_music_keywords(self, text: str) -> int:
        """Count number of music keywords found in text."""
        count = 0
        for keyword in self.music_keywords:
            if keyword in text:
                count += 1
        return count

    def _get_duration_score(self, duration: int | None) -> float:
        """
        Get a score based on video duration.

        IMPORTANT: Duration alone is a SECONDARY signal, not enough to classify.
        Other signals (identity, face, keywords) are required.

        Returns:
            Float between -0.5 and 0.25 (reduced range)
            Positive = slight boost for preaching
            Negative = penalty for likely music
        """
        if duration is None:
            return 0.0

        # Very long videos get a small boost (NOT enough alone)
        if duration >= self.config["likely_sermon_duration"]:
            return 0.25  # Reduced from 0.8

        # Long videos get minimal boost
        if duration >= self.config["min_sermon_duration"]:
            return 0.15  # Reduced from 0.5

        # Medium length - neutral
        if duration > self.config["max_music_duration"]:
            return 0.0  # Reduced from 0.2

        # Short videos penalized more
        if duration <= self.config["short_clip_duration"]:
            return -0.5  # Increased penalty from -0.4

        # Short-ish videos
        return -0.3  # Increased penalty from -0.2

    def _calculate_classification(
        self,
        preaching_score: int,
        music_score: int,
        duration_score: float,
        face_verified: bool,
        has_identity: bool = False,
        identity_boost: float = 0.0,
        channel_trust_level: int = 0
    ) -> Tuple[ContentType, float]:
        """
        Calculate final classification based on all factors using multi-signal approach.

        Multi-signal requirement: Need at least 2 positive signals for PREACHING.

        Signal weights:
            - Face verified: +2
            - Identity markers found: +2
            - 3+ preaching keywords: +1
            - Trusted/verified channel: +1
            - Long duration: +0.5

        Returns:
            Tuple of (ContentType, confidence_score)
        """
        # Face verification is the strongest signal
        if face_verified:
            return ContentType.PREACHING, 0.98

        # --- Count positive signals ---
        signals = 0.0

        if has_identity:
            signals += 2.0  # Strong signal

        if preaching_score >= 3:
            signals += 1.0  # Moderate signal

        if channel_trust_level >= 2:  # Trusted or verified channel
            signals += 1.0  # Moderate signal

        if duration_score >= 0.15:
            signals += 0.5  # Weak signal

        # Strong music indicators - classify as MUSIC
        if music_score >= 2 and preaching_score == 0:
            return ContentType.MUSIC, min(0.9, 0.6 + abs(duration_score) * 0.2)

        # --- STRICT MODE: Require identity markers ---
        if IDENTITY_MARKERS.get("strict_mode", True):
            if not has_identity and channel_trust_level < 2:
                # No identity markers and not a trusted channel = UNKNOWN
                return ContentType.UNKNOWN, 0.25

        # --- Multi-signal requirement: Need at least 2 signals for PREACHING ---
        if signals < 2:
            confidence = max(0.30, 0.25 + signals * 0.1)
            return ContentType.UNKNOWN, confidence

        # Strong preaching indicators with identity
        if preaching_score >= 3 and music_score == 0 and has_identity:
            confidence = min(0.95, 0.75 + identity_boost + duration_score * 0.1)
            return ContentType.PREACHING, confidence

        # Identity + keywords + duration
        if has_identity and preaching_score > music_score:
            confidence = 0.60 + identity_boost + (preaching_score - music_score) * 0.05
            confidence += duration_score * 0.1
            return ContentType.PREACHING, min(0.90, max(0.55, confidence))

        # Trusted channel with keywords
        if channel_trust_level >= 2 and preaching_score > music_score:
            confidence = 0.55 + (preaching_score - music_score) * 0.08
            confidence += duration_score * 0.1
            return ContentType.PREACHING, min(0.85, max(0.50, confidence))

        # Music wins by margin
        if music_score > preaching_score + 1:
            confidence = 0.5 + (music_score - preaching_score) * 0.1
            return ContentType.MUSIC, min(0.85, max(0.4, confidence))

        # Preaching wins by margin but no identity
        if preaching_score > music_score + 1:
            # Lower confidence without identity
            confidence = 0.40 + (preaching_score - music_score) * 0.05
            return ContentType.UNKNOWN, min(0.55, confidence)

        # Short video penalty
        if duration_score <= -0.3:
            return ContentType.MUSIC, 0.5 + abs(duration_score) * 0.15

        # Truly uncertain
        if preaching_score > music_score:
            return ContentType.UNKNOWN, 0.40
        elif music_score > preaching_score:
            return ContentType.MUSIC, 0.45
        else:
            return ContentType.UNKNOWN, 0.30

    def _detect_language(self, text: str) -> Language:
        """
        Detect whether the video is primarily French or English.

        Returns:
            Language enum (FR, EN, or UNKNOWN)
        """
        words = set(re.findall(r'\b\w+\b', text.lower()))

        french_count = len(words & self.french_words)
        english_count = len(words & self.english_words)

        # Need clear majority
        if french_count > english_count + 2:
            return Language.FRENCH
        elif english_count > french_count + 2:
            return Language.ENGLISH

        # Check for specific strong indicators
        if any(w in text for w in ["predication", "culte", "enseignement", "priere"]):
            return Language.FRENCH
        if any(w in text for w in ["preaching", "sermon", "service", "teaching"]):
            return Language.ENGLISH

        return Language.UNKNOWN

    def batch_classify(self, videos: list[VideoMetadata]) -> list[VideoMetadata]:
        """
        Classify multiple videos.

        Args:
            videos: List of VideoMetadata objects

        Returns:
            List of classified VideoMetadata objects
        """
        return [self.classify(video) for video in videos]

    def get_classification_summary(
        self, videos: list[VideoMetadata]
    ) -> dict:
        """
        Get summary statistics for classified videos.

        Returns:
            Dictionary with counts by content type
        """
        summary = {
            "total": len(videos),
            "preaching": 0,
            "music": 0,
            "unknown": 0,
            "needs_review": 0,
            "high_confidence": 0,
            "low_confidence": 0,
        }

        for video in videos:
            if video.content_type == ContentType.PREACHING:
                summary["preaching"] += 1
            elif video.content_type == ContentType.MUSIC:
                summary["music"] += 1
            else:
                summary["unknown"] += 1

            if video.needs_review:
                summary["needs_review"] += 1

            if video.confidence_score >= self.config["high_confidence"]:
                summary["high_confidence"] += 1
            elif video.confidence_score < self.config["low_confidence"]:
                summary["low_confidence"] += 1

        return summary


def classify_video(
    video: VideoMetadata,
    preacher_id: Optional[int] = None,
    preacher: Optional[Preacher] = None
) -> VideoMetadata:
    """
    Convenience function to classify a single video.

    Args:
        video: VideoMetadata to classify
        preacher_id: Optional preacher ID for preacher-specific classification
        preacher: Optional Preacher object

    Returns:
        Classified VideoMetadata
    """
    classifier = ContentClassifier(preacher_id=preacher_id, preacher=preacher)
    return classifier.classify(video)


def classify_videos(
    videos: list[VideoMetadata],
    preacher_id: Optional[int] = None,
    preacher: Optional[Preacher] = None
) -> list[VideoMetadata]:
    """
    Convenience function to classify multiple videos.

    Args:
        videos: List of VideoMetadata objects
        preacher_id: Optional preacher ID for preacher-specific classification
        preacher: Optional Preacher object

    Returns:
        List of classified VideoMetadata objects
    """
    classifier = ContentClassifier(preacher_id=preacher_id, preacher=preacher)
    return classifier.batch_classify(videos)


def get_classifier_for_preacher(preacher_id: int) -> ContentClassifier:
    """
    Get a content classifier configured for a specific preacher.

    Args:
        preacher_id: ID of the preacher

    Returns:
        ContentClassifier instance configured for the preacher
    """
    return ContentClassifier(preacher_id=preacher_id)
