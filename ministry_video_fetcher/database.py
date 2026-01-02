"""
Database Module for Ministry Video Fetcher

Handles all SQLite database operations including creating tables,
storing videos, and querying data.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
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

        conn.commit()
        conn.close()

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


# Convenience functions for quick access
def get_db(db_path: Optional[str] = None) -> Database:
    """Get a Database instance."""
    return Database(db_path)
