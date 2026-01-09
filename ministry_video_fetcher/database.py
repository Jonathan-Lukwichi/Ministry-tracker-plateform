"""
Database Module for Ministry Video Fetcher

Handles all SQLite database operations including creating tables,
storing videos, and querying data.

Supports multi-preacher architecture with preacher-specific video tracking.
"""

import sqlite3
import json
import os
import shutil
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import pandas as pd

from models import VideoMetadata, FetchLog, ContentType, Language
from config import DATABASE_CONFIG


class Database:
    """
    SQLite database handler for ministry videos.

    Provides methods for storing and querying video metadata,
    with support for pandas DataFrame operations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Uses config default if None.
        """
        self.db_path = db_path or DATABASE_CONFIG["db_path"]
        self._ensure_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                duration INTEGER,
                upload_date TEXT,
                view_count INTEGER,
                like_count INTEGER,
                thumbnail_url TEXT,
                channel_name TEXT,
                channel_id TEXT,
                channel_url TEXT,
                video_url TEXT,
                content_type TEXT DEFAULT 'UNKNOWN',
                confidence_score REAL DEFAULT 0.0,
                needs_review INTEGER DEFAULT 1,
                language_detected TEXT DEFAULT 'UNKNOWN',
                fetched_at TEXT,
                search_query_used TEXT
            )
        """)

        # Add new columns if they don't exist (for migration)
        cursor.execute("PRAGMA table_info(videos)")
        columns = [col[1] for col in cursor.fetchall()]

        if "face_verified" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN face_verified INTEGER DEFAULT 0")

        if "identity_matched" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN identity_matched INTEGER DEFAULT 0")

        if "channel_trust_level" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN channel_trust_level INTEGER DEFAULT 0")

        if "platform" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN platform TEXT DEFAULT 'youtube'")

        # Fetch logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fetch_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fetch_timestamp TEXT NOT NULL,
                query_used TEXT NOT NULL,
                videos_found INTEGER DEFAULT 0,
                videos_added INTEGER DEFAULT 0,
                videos_skipped INTEGER DEFAULT 0,
                music_excluded INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                error_messages TEXT
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_upload_date
            ON videos(upload_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_content_type
            ON videos(content_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_channel_name
            ON videos(channel_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_needs_review
            ON videos(needs_review)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_platform
            ON videos(platform)
        """)

        # =====================================================================
        # PREACHERS TABLE (Multi-preacher support)
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                aliases TEXT,
                title TEXT,
                primary_church TEXT,
                bio TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT
            )
        """)

        # Preacher face reference photos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preacher_face_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preacher_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                original_filename TEXT,
                file_size INTEGER,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (preacher_id) REFERENCES preachers(id) ON DELETE CASCADE
            )
        """)

        # Add preacher_id to videos table if not exists
        if "preacher_id" not in columns:
            cursor.execute("ALTER TABLE videos ADD COLUMN preacher_id INTEGER")

        # Create index for preacher filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_videos_preacher
            ON videos(preacher_id)
        """)

        # Run migration to set up initial preacher data
        self._migrate_initial_preacher(cursor)

        # =====================================================================
        # DISCOVERED CHANNELS TABLE (Facebook Agent)
        # =====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discovered_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL DEFAULT 'facebook',
                channel_name TEXT NOT NULL,
                channel_url TEXT NOT NULL UNIQUE,
                page_id TEXT,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_scanned TEXT,
                video_count INTEGER DEFAULT 0,
                preacher_id INTEGER,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                FOREIGN KEY (preacher_id) REFERENCES preachers(id)
            )
        """)

        # Create index for discovered channels
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_discovered_channels_platform
            ON discovered_channels(platform)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_discovered_channels_preacher
            ON discovered_channels(preacher_id)
        """)

        conn.commit()
        conn.close()

    def _migrate_initial_preacher(self, cursor):
        """
        Migration: Create initial preacher (Apostle Narcisse Majila) if not exists.
        Assigns existing videos and photos to preacher_id=1.
        """
        # Check if preachers table is empty
        cursor.execute("SELECT COUNT(*) as count FROM preachers")
        preacher_count = cursor.fetchone()["count"]

        if preacher_count == 0:
            # Create the initial preacher (Apostle Narcisse Majila)
            aliases = json.dumps([
                "Narcisse Majila",
                "Apotre Narcisse Majila",
                "Apôtre Narcisse Majila",
                "Pastor Narcisse Majila",
                "Pasteur Narcisse Majila",
                "Apostle Majila",
                "Apotre Majila",
                "Naricisse Majila",
            ])

            cursor.execute("""
                INSERT INTO preachers (name, aliases, title, primary_church, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                "Narcisse Majila",
                aliases,
                "Apostle",
                "Ramah Full Gospel Church Pretoria",
                datetime.now().isoformat()
            ))

            preacher_id = cursor.lastrowid
            print(f"Created initial preacher: Apostle Narcisse Majila (id={preacher_id})")

            # Update all existing videos to belong to this preacher
            cursor.execute(
                "UPDATE videos SET preacher_id = ? WHERE preacher_id IS NULL",
                (preacher_id,)
            )
            updated_count = cursor.rowcount
            if updated_count > 0:
                print(f"Assigned {updated_count} existing videos to preacher_id={preacher_id}")

            # Migrate existing photos to preacher-specific directory
            self._migrate_photos_for_preacher(cursor, preacher_id)

    def _migrate_photos_for_preacher(self, cursor, preacher_id: int):
        """Migrate existing photos from photos/ to photos/preacher_{id}/"""
        # Get project root directory
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(module_dir)
        old_photos_dir = os.path.join(project_dir, "photos")
        new_photos_dir = os.path.join(project_dir, "photos", f"preacher_{preacher_id}")

        # Check if old photos directory exists and has photos
        if not os.path.isdir(old_photos_dir):
            return

        # Find existing photos (not in subdirectories)
        photo_patterns = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        existing_photos = []
        for pattern in photo_patterns:
            existing_photos.extend(glob.glob(os.path.join(old_photos_dir, pattern)))

        if not existing_photos:
            return

        # Create preacher-specific directory
        os.makedirs(new_photos_dir, exist_ok=True)

        # Move photos and create database records
        for photo_path in existing_photos:
            filename = os.path.basename(photo_path)
            new_path = os.path.join(new_photos_dir, filename)

            try:
                # Move the file
                shutil.move(photo_path, new_path)

                # Get file size
                file_size = os.path.getsize(new_path)

                # Insert into database
                cursor.execute("""
                    INSERT INTO preacher_face_references
                    (preacher_id, file_path, original_filename, file_size, uploaded_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    preacher_id,
                    new_path,
                    filename,
                    file_size,
                    datetime.now().isoformat()
                ))

                print(f"Migrated photo: {filename} -> preacher_{preacher_id}/")
            except Exception as e:
                print(f"Error migrating photo {filename}: {e}")

    # =========================================================================
    # VIDEO OPERATIONS
    # =========================================================================

    def video_exists(self, video_id: str) -> bool:
        """Check if a video already exists in the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def insert_video(self, video: VideoMetadata) -> bool:
        """
        Insert a video into the database.

        Args:
            video: VideoMetadata object to insert

        Returns:
            True if inserted, False if duplicate
        """
        if self.video_exists(video.video_id):
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        data = video.to_dict()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])

        cursor.execute(
            f"INSERT INTO videos ({columns}) VALUES ({placeholders})",
            list(data.values())
        )

        conn.commit()
        conn.close()
        return True

    def insert_videos_batch(self, videos: List[VideoMetadata]) -> Tuple[int, int]:
        """
        Insert multiple videos, skipping duplicates.

        Args:
            videos: List of VideoMetadata objects

        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        inserted = 0
        skipped = 0

        conn = self._get_connection()
        cursor = conn.cursor()

        for video in videos:
            if self.video_exists(video.video_id):
                skipped += 1
                continue

            data = video.to_dict()
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])

            try:
                cursor.execute(
                    f"INSERT INTO videos ({columns}) VALUES ({placeholders})",
                    list(data.values())
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1

        conn.commit()
        conn.close()
        return inserted, skipped

    def update_video(self, video: VideoMetadata) -> bool:
        """Update an existing video's metadata."""
        conn = self._get_connection()
        cursor = conn.cursor()

        data = video.to_dict()
        video_id = data.pop("video_id")

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])

        cursor.execute(
            f"UPDATE videos SET {set_clause} WHERE video_id = ?",
            list(data.values()) + [video_id]
        )

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def mark_as_reviewed(
        self, video_id: str, content_type: ContentType
    ) -> bool:
        """
        Manually mark a video as reviewed with corrected classification.

        Args:
            video_id: The video to update
            content_type: The correct content type

        Returns:
            True if updated successfully
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE videos
               SET content_type = ?, needs_review = 0, confidence_score = 1.0
               WHERE video_id = ?""",
            (content_type.value, video_id)
        )

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_video(self, video_id: str) -> bool:
        """Delete a video from the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_short_videos(self, max_duration: int = 600) -> int:
        """
        Delete all videos shorter than a given duration.

        Args:
            max_duration: Maximum duration in seconds to keep (default: 600s = 10 mins)

        Returns:
            Number of videos deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM videos WHERE duration < ?", (max_duration,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected

    def delete_low_confidence_videos(self, min_confidence: float = 0.50) -> int:
        """
        Delete all videos with confidence score below threshold.

        Args:
            min_confidence: Minimum confidence to keep (default: 0.50)

        Returns:
            Number of videos deleted
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM videos WHERE confidence_score < ?",
            (min_confidence,)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected

    def update_video_classification(
        self,
        video_id: str,
        content_type: "ContentType",
        confidence_score: float,
        needs_review: bool,
        identity_matched: bool = False,
        channel_trust_level: int = 0
    ) -> bool:
        """
        Update video classification fields.

        Args:
            video_id: YouTube video ID
            content_type: ContentType enum
            confidence_score: New confidence score
            needs_review: Whether video needs manual review
            identity_matched: Whether identity markers were found
            channel_trust_level: Channel trust level (0-3)

        Returns:
            True if video was updated
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE videos SET
                content_type = ?,
                confidence_score = ?,
                needs_review = ?,
                identity_matched = ?,
                channel_trust_level = ?
               WHERE video_id = ?""",
            (
                content_type.value if hasattr(content_type, 'value') else str(content_type),
                confidence_score,
                1 if needs_review else 0,
                1 if identity_matched else 0,
                channel_trust_level,
                video_id
            )
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    # =========================================================================
    # QUERY METHODS
    # =========================================================================

    def get_all_sermons(self) -> pd.DataFrame:
        """
        Get all preaching videos as a DataFrame.

        Returns:
            DataFrame with all PREACHING and UNKNOWN content types
        """
        conn = self._get_connection()
        df = pd.read_sql_query(
            """SELECT * FROM videos
               WHERE content_type IN ('PREACHING', 'UNKNOWN')
               ORDER BY upload_date DESC""",
            conn
        )
        conn.close()
        return df

    def get_sermons_by_channel(self, channel_name: str) -> pd.DataFrame:
        """Get sermons from a specific channel."""
        conn = self._get_connection()
        df = pd.read_sql_query(
            """SELECT * FROM videos
               WHERE channel_name LIKE ?
               AND content_type IN ('PREACHING', 'UNKNOWN')
               ORDER BY upload_date DESC""",
            conn,
            params=(f"%{channel_name}%",)
        )
        conn.close()
        return df

    def get_sermons_by_year(self, year: int) -> pd.DataFrame:
        """Get sermons from a specific year."""
        conn = self._get_connection()
        df = pd.read_sql_query(
            """SELECT * FROM videos
               WHERE upload_date LIKE ?
               AND content_type IN ('PREACHING', 'UNKNOWN')
               ORDER BY upload_date DESC""",
            conn,
            params=(f"{year}%",)
        )
        conn.close()
        return df

    def get_sermons_by_language(self, lang: str) -> pd.DataFrame:
        """Get sermons by detected language (FR or EN)."""
        conn = self._get_connection()
        df = pd.read_sql_query(
            """SELECT * FROM videos
               WHERE language_detected = ?
               AND content_type IN ('PREACHING', 'UNKNOWN')
               ORDER BY upload_date DESC""",
            conn,
            params=(lang.upper(),)
        )
        conn.close()
        return df

    def get_review_queue(self) -> pd.DataFrame:
        """Get videos that need manual review."""
        conn = self._get_connection()
        df = pd.read_sql_query(
            """SELECT video_id, title, channel_name, duration,
                      content_type, confidence_score, video_url
               FROM videos
               WHERE needs_review = 1
               ORDER BY confidence_score ASC""",
            conn
        )
        conn.close()
        return df

    def get_video_by_id(self, video_id: str) -> Optional[VideoMetadata]:
        """Get a single video by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return VideoMetadata.from_dict(dict(row))
        return None

    # =========================================================================
    # STATISTICS METHODS
    # =========================================================================

    def get_total_preaching_hours(self) -> float:
        """Get total duration of all preaching videos in hours."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT SUM(duration) as total
               FROM videos
               WHERE content_type IN ('PREACHING', 'UNKNOWN')
               AND duration IS NOT NULL"""
        )
        result = cursor.fetchone()
        conn.close()

        if result and result["total"]:
            return result["total"] / 3600  # Convert seconds to hours
        return 0.0

    def get_channel_breakdown(self) -> List[Tuple[str, int]]:
        """Get count of videos per channel."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT channel_name, COUNT(*) as count
               FROM videos
               WHERE content_type IN ('PREACHING', 'UNKNOWN')
               GROUP BY channel_name
               ORDER BY count DESC"""
        )
        results = cursor.fetchall()
        conn.close()
        return [(row["channel_name"], row["count"]) for row in results]

    def get_statistics(self) -> dict:
        """Get comprehensive database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total videos
        cursor.execute("SELECT COUNT(*) as count FROM videos")
        stats["total_videos"] = cursor.fetchone()["count"]

        # By content type
        cursor.execute(
            """SELECT content_type, COUNT(*) as count
               FROM videos GROUP BY content_type"""
        )
        stats["by_content_type"] = {
            row["content_type"]: row["count"] for row in cursor.fetchall()
        }

        # By language
        cursor.execute(
            """SELECT language_detected, COUNT(*) as count
               FROM videos GROUP BY language_detected"""
        )
        stats["by_language"] = {
            row["language_detected"]: row["count"] for row in cursor.fetchall()
        }

        # Needs review count
        cursor.execute(
            "SELECT COUNT(*) as count FROM videos WHERE needs_review = 1"
        )
        stats["needs_review"] = cursor.fetchone()["count"]

        # Unique channels
        cursor.execute("SELECT COUNT(DISTINCT channel_name) as count FROM videos")
        stats["unique_channels"] = cursor.fetchone()["count"]

        # Date range
        cursor.execute(
            """SELECT MIN(upload_date) as oldest, MAX(upload_date) as newest
               FROM videos WHERE upload_date IS NOT NULL"""
        )
        row = cursor.fetchone()
        stats["oldest_video"] = row["oldest"]
        stats["newest_video"] = row["newest"]

        # Total hours
        stats["total_hours"] = self.get_total_preaching_hours()

        # Top channels
        stats["top_channels"] = self.get_channel_breakdown()[:10]

        conn.close()
        return stats

    def get_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        """Get oldest and newest video dates."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT MIN(upload_date) as oldest, MAX(upload_date) as newest
               FROM videos
               WHERE upload_date IS NOT NULL
               AND content_type IN ('PREACHING', 'UNKNOWN')"""
        )
        row = cursor.fetchone()
        conn.close()
        return row["oldest"], row["newest"]

    def get_unique_channels_count(self) -> int:
        """Get count of unique channels."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT COUNT(DISTINCT channel_name) as count
               FROM videos
               WHERE content_type IN ('PREACHING', 'UNKNOWN')"""
        )
        result = cursor.fetchone()["count"]
        conn.close()
        return result

    def get_review_count(self) -> int:
        """Get count of videos needing review."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM videos WHERE needs_review = 1"
        )
        result = cursor.fetchone()["count"]
        conn.close()
        return result

    # =========================================================================
    # PLATFORM-SPECIFIC METHODS
    # =========================================================================

    def get_sermons_by_platform(self, platform: str) -> pd.DataFrame:
        """Get sermons from a specific platform (youtube or facebook)."""
        conn = self._get_connection()
        df = pd.read_sql_query(
            """SELECT * FROM videos
               WHERE (platform = ? OR (platform IS NULL AND ? = 'youtube'))
               AND content_type IN ('PREACHING', 'UNKNOWN')
               ORDER BY upload_date DESC""",
            conn,
            params=(platform, platform)
        )
        conn.close()
        return df

    def get_platform_statistics(self) -> dict:
        """Get video count breakdown by platform."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Count by platform
        cursor.execute(
            """SELECT
                COALESCE(platform, 'youtube') as platform,
                COUNT(*) as count
               FROM videos
               WHERE content_type IN ('PREACHING', 'UNKNOWN')
               GROUP BY COALESCE(platform, 'youtube')"""
        )
        for row in cursor.fetchall():
            stats[row["platform"]] = row["count"]

        # Total hours by platform
        cursor.execute(
            """SELECT
                COALESCE(platform, 'youtube') as platform,
                SUM(duration) / 3600.0 as hours
               FROM videos
               WHERE content_type IN ('PREACHING', 'UNKNOWN')
               AND duration IS NOT NULL
               GROUP BY COALESCE(platform, 'youtube')"""
        )
        stats["hours_by_platform"] = {}
        for row in cursor.fetchall():
            stats["hours_by_platform"][row["platform"]] = round(row["hours"] or 0, 1)

        conn.close()
        return stats

    def get_video_count_by_platform(self, platform: str) -> int:
        """Get count of videos from a specific platform."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT COUNT(*) as count FROM videos
               WHERE (platform = ? OR (platform IS NULL AND ? = 'youtube'))
               AND content_type IN ('PREACHING', 'UNKNOWN')""",
            (platform, platform)
        )
        result = cursor.fetchone()["count"]
        conn.close()
        return result

    # =========================================================================
    # FACE VERIFICATION METHODS
    # =========================================================================

    def get_videos_for_face_verification(
        self,
        only_unverified: bool = True,
        channel_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[VideoMetadata]:
        """
        Get videos that need face verification.

        Args:
            only_unverified: If True, only get videos where face_verified = 0
            channel_filter: Optional channel name to filter by
            limit: Optional max number of videos to return

        Returns:
            List of VideoMetadata objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM videos WHERE 1=1"
        params = []

        if only_unverified:
            query += " AND (face_verified = 0 OR face_verified IS NULL)"

        if channel_filter:
            query += " AND channel_name LIKE ?"
            params.append(f"%{channel_filter}%")

        query += " ORDER BY upload_date DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [VideoMetadata.from_dict(dict(row)) for row in rows]

    def update_face_verification(
        self,
        video_id: str,
        face_verified: bool,
        confidence_score: Optional[float] = None,
        content_type: Optional[ContentType] = None,
        needs_review: Optional[bool] = None
    ) -> bool:
        """
        Update face verification status for a video.

        Args:
            video_id: The video to update
            face_verified: Whether face was verified
            confidence_score: Optional new confidence score
            content_type: Optional new content type
            needs_review: Optional new review status

        Returns:
            True if updated successfully
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        updates = ["face_verified = ?"]
        params = [1 if face_verified else 0]

        if confidence_score is not None:
            updates.append("confidence_score = ?")
            params.append(confidence_score)

        if content_type is not None:
            updates.append("content_type = ?")
            params.append(content_type.value)

        if needs_review is not None:
            updates.append("needs_review = ?")
            params.append(1 if needs_review else 0)

        params.append(video_id)

        cursor.execute(
            f"UPDATE videos SET {', '.join(updates)} WHERE video_id = ?",
            params
        )

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def get_face_verification_stats(self) -> dict:
        """Get statistics about face verification status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total videos
        cursor.execute("SELECT COUNT(*) as count FROM videos")
        stats["total_videos"] = cursor.fetchone()["count"]

        # Face verified count
        cursor.execute("SELECT COUNT(*) as count FROM videos WHERE face_verified = 1")
        stats["face_verified"] = cursor.fetchone()["count"]

        # Not verified count
        cursor.execute("SELECT COUNT(*) as count FROM videos WHERE face_verified = 0 OR face_verified IS NULL")
        stats["not_verified"] = cursor.fetchone()["count"]

        # Verified preaching videos
        cursor.execute(
            """SELECT COUNT(*) as count FROM videos
               WHERE face_verified = 1 AND content_type = 'PREACHING'"""
        )
        stats["verified_preaching"] = cursor.fetchone()["count"]

        conn.close()
        return stats

    def get_video_count(
        self, content_type: Optional[ContentType] = None
    ) -> int:
        """Get total count of videos, optionally filtered by type."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if content_type:
            cursor.execute(
                "SELECT COUNT(*) as count FROM videos WHERE content_type = ?",
                (content_type.value,)
            )
        else:
            cursor.execute("SELECT COUNT(*) as count FROM videos")

        result = cursor.fetchone()["count"]
        conn.close()
        return result

    # =========================================================================
    # FETCH LOG OPERATIONS
    # =========================================================================

    def log_fetch(self, log: FetchLog) -> int:
        """
        Log a fetch operation.

        Returns:
            The ID of the created log entry
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO fetch_logs
               (fetch_timestamp, query_used, videos_found, videos_added,
                videos_skipped, music_excluded, errors_count, error_messages)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                log.fetch_timestamp.isoformat(),
                log.query_used,
                log.videos_found,
                log.videos_added,
                log.videos_skipped,
                log.music_excluded,
                log.errors_count,
                log.error_messages,
            )
        )

        conn.commit()
        log_id = cursor.lastrowid
        conn.close()
        return log_id

    def get_fetch_logs(self, limit: int = 20) -> pd.DataFrame:
        """Get recent fetch logs."""
        conn = self._get_connection()
        df = pd.read_sql_query(
            f"""SELECT * FROM fetch_logs
               ORDER BY fetch_timestamp DESC
               LIMIT {limit}""",
            conn
        )
        conn.close()
        return df

    # =========================================================================
    # EXPORT METHODS
    # =========================================================================

    def export_to_csv(self, filepath: str) -> int:
        """
        Export all preaching videos to CSV.

        Args:
            filepath: Path to save CSV file

        Returns:
            Number of rows exported
        """
        df = self.get_all_sermons()
        df.to_csv(filepath, index=False)
        return len(df)

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export all videos to DataFrame."""
        conn = self._get_connection()
        df = pd.read_sql_query("SELECT * FROM videos ORDER BY upload_date DESC", conn)
        conn.close()
        return df


    # =========================================================================
    # PREACHER CRUD OPERATIONS
    # =========================================================================

    def create_preacher(
        self,
        name: str,
        aliases: List[str],
        title: Optional[str] = None,
        primary_church: Optional[str] = None,
        bio: Optional[str] = None
    ) -> int:
        """
        Create a new preacher.

        Args:
            name: Full name of the preacher
            aliases: List of name variations for search
            title: Title (Apostle, Pastor, etc.)
            primary_church: Primary church name
            bio: Biography text

        Returns:
            The ID of the created preacher
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO preachers (name, aliases, title, primary_church, bio, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            json.dumps(aliases),
            title,
            primary_church,
            bio,
            datetime.now().isoformat()
        ))

        conn.commit()
        preacher_id = cursor.lastrowid
        conn.close()

        # Create photos directory for this preacher
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(module_dir)
        photos_dir = os.path.join(project_dir, "photos", f"preacher_{preacher_id}")
        os.makedirs(photos_dir, exist_ok=True)

        return preacher_id

    def get_preacher(self, preacher_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a preacher by ID.

        Returns:
            Dict with preacher data or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM preachers WHERE id = ?", (preacher_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            data = dict(row)
            data["aliases"] = json.loads(data["aliases"]) if data["aliases"] else []
            return data
        return None

    def get_preacher_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a preacher by name (case-insensitive partial match)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM preachers WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{name}%",)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            data = dict(row)
            data["aliases"] = json.loads(data["aliases"]) if data["aliases"] else []
            return data
        return None

    def get_all_preachers(self) -> List[Dict[str, Any]]:
        """Get all preachers with video counts."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*,
                   COUNT(DISTINCT v.video_id) as video_count,
                   COALESCE(SUM(v.duration) / 3600.0, 0) as total_hours
            FROM preachers p
            LEFT JOIN videos v ON p.id = v.preacher_id
                AND v.content_type IN ('PREACHING', 'UNKNOWN')
            WHERE p.is_active = 1
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """)

        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["aliases"] = json.loads(data["aliases"]) if data["aliases"] else []
            data["total_hours"] = round(data["total_hours"], 1)
            results.append(data)

        conn.close()
        return results

    def update_preacher(
        self,
        preacher_id: int,
        name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        title: Optional[str] = None,
        primary_church: Optional[str] = None,
        bio: Optional[str] = None
    ) -> bool:
        """Update a preacher's information."""
        conn = self._get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if aliases is not None:
            updates.append("aliases = ?")
            params.append(json.dumps(aliases))
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if primary_church is not None:
            updates.append("primary_church = ?")
            params.append(primary_church)
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(preacher_id)

        cursor.execute(
            f"UPDATE preachers SET {', '.join(updates)} WHERE id = ?",
            params
        )

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_preacher(self, preacher_id: int) -> bool:
        """
        Soft delete a preacher (set is_active = 0).
        Does not delete associated videos or photos.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE preachers SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), preacher_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    # =========================================================================
    # PREACHER FACE REFERENCE OPERATIONS
    # =========================================================================

    def add_face_reference(
        self,
        preacher_id: int,
        file_path: str,
        original_filename: str,
        file_size: int
    ) -> int:
        """
        Add a face reference photo for a preacher.

        Returns:
            The ID of the created reference
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO preacher_face_references
            (preacher_id, file_path, original_filename, file_size, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            preacher_id,
            file_path,
            original_filename,
            file_size,
            datetime.now().isoformat()
        ))

        conn.commit()
        ref_id = cursor.lastrowid
        conn.close()
        return ref_id

    def get_face_references(self, preacher_id: int) -> List[Dict[str, Any]]:
        """Get all face reference photos for a preacher."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM preacher_face_references
            WHERE preacher_id = ?
            ORDER BY uploaded_at DESC
        """, (preacher_id,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def delete_face_reference(self, reference_id: int) -> bool:
        """Delete a face reference photo record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get the file path before deleting
        cursor.execute(
            "SELECT file_path FROM preacher_face_references WHERE id = ?",
            (reference_id,)
        )
        row = cursor.fetchone()

        if row:
            # Delete the record
            cursor.execute(
                "DELETE FROM preacher_face_references WHERE id = ?",
                (reference_id,)
            )
            conn.commit()
            affected = cursor.rowcount

            # Delete the actual file
            if row["file_path"] and os.path.exists(row["file_path"]):
                try:
                    os.remove(row["file_path"])
                except Exception as e:
                    print(f"Warning: Could not delete file {row['file_path']}: {e}")

            conn.close()
            return affected > 0

        conn.close()
        return False

    def get_face_reference_count(self, preacher_id: int) -> int:
        """Get count of face reference photos for a preacher."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM preacher_face_references WHERE preacher_id = ?",
            (preacher_id,)
        )
        result = cursor.fetchone()["count"]
        conn.close()
        return result

    # =========================================================================
    # PREACHER-FILTERED VIDEO QUERIES
    # =========================================================================

    def get_videos_by_preacher(
        self,
        preacher_id: int,
        limit: int = 100,
        content_types: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get videos for a specific preacher.

        Args:
            preacher_id: The preacher's ID
            limit: Maximum number of videos to return
            content_types: Filter by content types (default: PREACHING, UNKNOWN)

        Returns:
            DataFrame with video data
        """
        if content_types is None:
            content_types = ['PREACHING', 'UNKNOWN']

        conn = self._get_connection()
        placeholders = ','.join('?' * len(content_types))

        df = pd.read_sql_query(
            f"""SELECT * FROM videos
               WHERE preacher_id = ?
               AND content_type IN ({placeholders})
               ORDER BY upload_date DESC
               LIMIT ?""",
            conn,
            params=[preacher_id] + content_types + [limit]
        )
        conn.close()
        return df

    def get_statistics_for_preacher(self, preacher_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific preacher."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {"preacher_id": preacher_id}

        # Total videos
        cursor.execute(
            "SELECT COUNT(*) as count FROM videos WHERE preacher_id = ?",
            (preacher_id,)
        )
        stats["total_videos"] = cursor.fetchone()["count"]

        # By content type
        cursor.execute("""
            SELECT content_type, COUNT(*) as count
            FROM videos WHERE preacher_id = ?
            GROUP BY content_type
        """, (preacher_id,))
        stats["by_content_type"] = {
            row["content_type"]: row["count"] for row in cursor.fetchall()
        }

        # By language
        cursor.execute("""
            SELECT language_detected, COUNT(*) as count
            FROM videos WHERE preacher_id = ?
            GROUP BY language_detected
        """, (preacher_id,))
        stats["by_language"] = {
            row["language_detected"]: row["count"] for row in cursor.fetchall()
        }

        # Needs review count
        cursor.execute("""
            SELECT COUNT(*) as count FROM videos
            WHERE preacher_id = ? AND needs_review = 1
        """, (preacher_id,))
        stats["needs_review"] = cursor.fetchone()["count"]

        # Unique channels
        cursor.execute("""
            SELECT COUNT(DISTINCT channel_name) as count
            FROM videos WHERE preacher_id = ?
        """, (preacher_id,))
        stats["unique_channels"] = cursor.fetchone()["count"]

        # Date range
        cursor.execute("""
            SELECT MIN(upload_date) as oldest, MAX(upload_date) as newest
            FROM videos
            WHERE preacher_id = ? AND upload_date IS NOT NULL
        """, (preacher_id,))
        row = cursor.fetchone()
        stats["oldest_video"] = row["oldest"]
        stats["newest_video"] = row["newest"]

        # Total hours
        cursor.execute("""
            SELECT COALESCE(SUM(duration) / 3600.0, 0) as hours
            FROM videos
            WHERE preacher_id = ?
            AND content_type IN ('PREACHING', 'UNKNOWN')
            AND duration IS NOT NULL
        """, (preacher_id,))
        stats["total_hours"] = round(cursor.fetchone()["hours"], 1)

        # Top channels
        cursor.execute("""
            SELECT channel_name, COUNT(*) as count
            FROM videos
            WHERE preacher_id = ?
            AND content_type IN ('PREACHING', 'UNKNOWN')
            GROUP BY channel_name
            ORDER BY count DESC
            LIMIT 10
        """, (preacher_id,))
        stats["top_channels"] = [
            {"name": row["channel_name"], "count": row["count"]}
            for row in cursor.fetchall()
        ]

        # By platform
        cursor.execute("""
            SELECT COALESCE(platform, 'youtube') as platform, COUNT(*) as count
            FROM videos
            WHERE preacher_id = ?
            AND content_type IN ('PREACHING', 'UNKNOWN')
            GROUP BY COALESCE(platform, 'youtube')
        """, (preacher_id,))
        stats["by_platform"] = {
            row["platform"]: row["count"] for row in cursor.fetchall()
        }

        conn.close()
        return stats

    def get_video_count_by_preacher(self, preacher_id: int) -> int:
        """Get count of videos for a specific preacher."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count FROM videos
            WHERE preacher_id = ?
            AND content_type IN ('PREACHING', 'UNKNOWN')
        """, (preacher_id,))
        result = cursor.fetchone()["count"]
        conn.close()
        return result

    def get_preaching_hours_by_preacher(self, preacher_id: int) -> float:
        """Get total preaching hours for a specific preacher."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(duration) / 3600.0, 0) as hours
            FROM videos
            WHERE preacher_id = ?
            AND content_type IN ('PREACHING', 'UNKNOWN')
            AND duration IS NOT NULL
        """, (preacher_id,))
        result = cursor.fetchone()["hours"]
        conn.close()
        return round(result, 1)

    def update_video_preacher(self, video_id: str, preacher_id: int) -> bool:
        """Assign a video to a preacher."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE videos SET preacher_id = ? WHERE video_id = ?",
            (preacher_id, video_id)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def get_recent_videos_by_preacher(
        self,
        preacher_id: int,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """Get recent videos for a preacher as a list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT video_id, title, thumbnail_url, duration, upload_date,
                   channel_name, video_url, view_count, platform
            FROM videos
            WHERE preacher_id = ?
            AND content_type IN ('PREACHING', 'UNKNOWN')
            ORDER BY upload_date DESC
            LIMIT ?
        """, (preacher_id, limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results


    # =========================================================================
    # DISCOVERED CHANNELS OPERATIONS (Facebook Agent)
    # =========================================================================

    def add_discovered_channel(
        self,
        channel_name: str,
        channel_url: str,
        platform: str = "facebook",
        page_id: Optional[str] = None,
        preacher_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[int]:
        """
        Add a newly discovered channel where the preacher appears.

        Args:
            channel_name: Name of the channel/page
            channel_url: URL to the channel
            platform: Platform (default: facebook)
            page_id: Platform-specific page ID
            preacher_id: Associated preacher ID
            notes: Optional notes

        Returns:
            The ID of the created channel, or None if already exists
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO discovered_channels
                (platform, channel_name, channel_url, page_id, preacher_id, notes, discovered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                platform,
                channel_name,
                channel_url,
                page_id,
                preacher_id,
                notes,
                datetime.now().isoformat()
            ))

            conn.commit()
            channel_id = cursor.lastrowid
            conn.close()
            return channel_id

        except sqlite3.IntegrityError:
            # Channel URL already exists
            conn.close()
            return None

    def get_discovered_channel_by_url(self, channel_url: str) -> Optional[Dict[str, Any]]:
        """Get a discovered channel by its URL."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM discovered_channels WHERE channel_url = ?",
            (channel_url,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def channel_exists(self, channel_url: str) -> bool:
        """Check if a channel URL is already in discovered channels."""
        return self.get_discovered_channel_by_url(channel_url) is not None

    def get_all_discovered_channels(
        self,
        platform: Optional[str] = None,
        preacher_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all discovered channels with optional filtering.

        Args:
            platform: Filter by platform (facebook, youtube)
            preacher_id: Filter by preacher
            active_only: Only return active channels

        Returns:
            List of channel dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM discovered_channels WHERE 1=1"
        params = []

        if active_only:
            query += " AND is_active = 1"

        if platform:
            query += " AND platform = ?"
            params.append(platform)

        if preacher_id:
            query += " AND preacher_id = ?"
            params.append(preacher_id)

        query += " ORDER BY video_count DESC, discovered_at DESC"

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def update_discovered_channel(
        self,
        channel_id: int,
        video_count: Optional[int] = None,
        last_scanned: Optional[str] = None,
        is_active: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update a discovered channel's information."""
        conn = self._get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if video_count is not None:
            updates.append("video_count = ?")
            params.append(video_count)

        if last_scanned is not None:
            updates.append("last_scanned = ?")
            params.append(last_scanned)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if not updates:
            conn.close()
            return False

        params.append(channel_id)

        cursor.execute(
            f"UPDATE discovered_channels SET {', '.join(updates)} WHERE id = ?",
            params
        )

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def increment_channel_video_count(self, channel_url: str, increment: int = 1) -> bool:
        """Increment the video count for a channel and update last_scanned."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE discovered_channels
            SET video_count = video_count + ?,
                last_scanned = ?
            WHERE channel_url = ?
        """, (increment, datetime.now().isoformat(), channel_url))

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_discovered_channel(self, channel_id: int) -> bool:
        """Delete a discovered channel (hard delete)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM discovered_channels WHERE id = ?",
            (channel_id,)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def get_discovered_channels_stats(self) -> Dict[str, Any]:
        """Get statistics about discovered channels."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total channels
        cursor.execute("SELECT COUNT(*) as count FROM discovered_channels WHERE is_active = 1")
        stats["total_channels"] = cursor.fetchone()["count"]

        # By platform
        cursor.execute("""
            SELECT platform, COUNT(*) as count
            FROM discovered_channels
            WHERE is_active = 1
            GROUP BY platform
        """)
        stats["by_platform"] = {
            row["platform"]: row["count"] for row in cursor.fetchall()
        }

        # Total videos discovered
        cursor.execute("""
            SELECT COALESCE(SUM(video_count), 0) as total
            FROM discovered_channels
            WHERE is_active = 1
        """)
        stats["total_videos_discovered"] = cursor.fetchone()["total"]

        # Recently discovered
        cursor.execute("""
            SELECT channel_name, channel_url, discovered_at, video_count
            FROM discovered_channels
            WHERE is_active = 1
            ORDER BY discovered_at DESC
            LIMIT 5
        """)
        stats["recent_discoveries"] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return stats


# Convenience functions for quick access
def get_db(db_path: Optional[str] = None) -> Database:
    """Get a Database instance."""
    return Database(db_path)
