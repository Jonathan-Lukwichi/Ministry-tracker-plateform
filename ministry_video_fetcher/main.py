#!/usr/bin/env python3
"""
Ministry Video Fetcher - Main Entry Point

A tool to fetch, classify, and track preaching videos of
Apostle Narcisse Majila from YouTube and Facebook.

Usage:
    python main.py fetch              - Run full fetch from YouTube (default)
    python main.py fetch --facebook   - Run fetch from Facebook only
    python main.py fetch --all        - Run fetch from all platforms
    python main.py stats              - Show database statistics
    python main.py review             - List videos flagged for review
    python main.py export             - Export to CSV
    python main.py sample             - Show sample videos
"""

import sys
import argparse
from datetime import datetime
from tabulate import tabulate

from database import Database
from fetcher import VideoFetcher
from models import ContentType
from config import EXPORT_CONFIG


def cmd_fetch(args):
    """Run fetch from specified platforms."""
    platform = getattr(args, 'platform', 'youtube')

    print("\n" + "=" * 60)
    print("MINISTRY VIDEO FETCHER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Platform: {platform.upper()}")
    print("=" * 60 + "\n")

    db = Database()
    fetcher = VideoFetcher(db)

    print(f"Starting video fetch from {platform}...")
    print("-" * 60)

    if platform == "youtube":
        summary = fetcher.fetch_all()
    elif platform == "facebook":
        summary = fetcher.fetch_facebook()
    elif platform == "all":
        summary = fetcher.fetch_all_platforms()
    else:
        print(f"Unknown platform: {platform}")
        return

    print("-" * 60)
    summary.print_summary()


def cmd_stats(args):
    """Show database statistics."""
    db = Database()
    stats = db.get_statistics()

    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    print(f"\nTotal videos in database: {stats['total_videos']}")

    print("\nBy Content Type:")
    for ctype, count in stats.get("by_content_type", {}).items():
        print(f"  {ctype}: {count}")

    print("\nBy Language:")
    for lang, count in stats.get("by_language", {}).items():
        print(f"  {lang}: {count}")

    print(f"\nVideos needing review: {stats['needs_review']}")
    print(f"Unique channels: {stats['unique_channels']}")

    if stats.get("oldest_video") and stats.get("newest_video"):
        oldest = format_date(stats["oldest_video"])
        newest = format_date(stats["newest_video"])
        print(f"Date range: {oldest} to {newest}")

    hours = stats.get("total_hours", 0)
    h = int(hours)
    m = int((hours - h) * 60)
    print(f"Total preaching hours: {h}h {m}m")

    if stats.get("top_channels"):
        print("\nTop 10 Channels:")
        for i, (channel, count) in enumerate(stats["top_channels"], 1):
            channel_name = channel or "Unknown"
            print(f"  {i:2}. {channel_name[:40]}: {count} videos")

    print("=" * 60 + "\n")


def cmd_review(args):
    """List videos flagged for review."""
    db = Database()
    df = db.get_review_queue()

    if df.empty:
        print("\nNo videos flagged for review.")
        return

    print("\n" + "=" * 60)
    print(f"VIDEOS NEEDING REVIEW ({len(df)} total)")
    print("=" * 60 + "\n")

    # Format for display
    display_data = []
    for _, row in df.iterrows():
        duration = format_duration(row.get("duration"))
        confidence = f"{row['confidence_score']:.2f}" if row.get("confidence_score") else "N/A"
        display_data.append([
            row["video_id"],
            row["title"][:50] + "..." if len(str(row["title"])) > 50 else row["title"],
            row["channel_name"][:25] if row.get("channel_name") else "Unknown",
            duration,
            row["content_type"],
            confidence,
        ])

    headers = ["Video ID", "Title", "Channel", "Duration", "Type", "Confidence"]
    print(tabulate(display_data[:20], headers=headers, tablefmt="simple"))

    if len(df) > 20:
        print(f"\n... and {len(df) - 20} more videos")

    print("\nTo mark a video as reviewed:")
    print("  from database import Database")
    print("  from models import ContentType")
    print("  db = Database()")
    print("  db.mark_as_reviewed('VIDEO_ID', ContentType.PREACHING)")


def cmd_export(args):
    """Export to CSV."""
    db = Database()
    filepath = args.output or EXPORT_CONFIG["csv_filename"]

    count = db.export_to_csv(filepath)
    print(f"\nExported {count} videos to {filepath}")


def cmd_sample(args):
    """Show sample videos from database."""
    db = Database()
    df = db.get_all_sermons()

    if df.empty:
        print("\nNo videos in database. Run 'python main.py fetch' first.")
        return

    # Show sample of preaching videos
    preaching_df = df[df["content_type"].isin(["PREACHING", "UNKNOWN"])]

    print("\n" + "=" * 60)
    print(f"SAMPLE PREACHING VIDEOS (Total: {len(preaching_df)})")
    print("=" * 60 + "\n")

    # Show 10 random samples
    sample = preaching_df.head(10)

    display_data = []
    for _, row in sample.iterrows():
        duration = format_duration(row.get("duration"))
        date = format_date(row.get("upload_date"))
        display_data.append([
            row["title"][:45] + "..." if len(str(row["title"])) > 45 else row["title"],
            row["channel_name"][:20] if row.get("channel_name") else "Unknown",
            duration,
            date,
            row["language_detected"],
        ])

    headers = ["Title", "Channel", "Duration", "Date", "Lang"]
    print(tabulate(display_data, headers=headers, tablefmt="simple"))


def cmd_channels(args):
    """Show channel breakdown."""
    db = Database()
    channels = db.get_channel_breakdown()

    if not channels:
        print("\nNo videos in database.")
        return

    print("\n" + "=" * 60)
    print("CHANNELS WHERE SERMONS APPEAR")
    print("=" * 60 + "\n")

    display_data = []
    for channel, count in channels:
        channel_name = channel or "Unknown"
        display_data.append([channel_name[:50], count])

    headers = ["Channel Name", "Video Count"]
    print(tabulate(display_data, headers=headers, tablefmt="simple"))
    print(f"\nTotal unique channels: {len(channels)}")


def cmd_mark_reviewed(args):
    """Mark a video as reviewed with correct classification."""
    db = Database()

    video_id = args.video_id
    content_type_str = args.content_type.upper()

    try:
        content_type = ContentType(content_type_str)
    except ValueError:
        print(f"Invalid content type: {content_type_str}")
        print("Valid types: PREACHING, MUSIC, UNKNOWN")
        return

    if db.mark_as_reviewed(video_id, content_type):
        print(f"Marked video {video_id} as {content_type.value}")
    else:
        print(f"Video {video_id} not found in database")


def cmd_cleanup_shorts(args):
    """Delete videos shorter than 10 minutes from the database."""
    db = Database()

    print("\n" + "=" * 60)
    print("CLEANING UP SHORT VIDEOS (< 10 minutes)")
    print("=" * 60)

    deleted_count = db.delete_short_videos(max_duration=600)

    if deleted_count > 0:
        print(f"\n[OK] Successfully deleted {deleted_count} short videos.")
    else:
        print("\nNo short videos found to delete.")

    print("=" * 60 + "\n")


def cmd_cleanup(args):
    """Clean up database: review, purge, or reclassify videos."""
    from classifier import ContentClassifier
    from config import STORAGE_CONFIG

    db = Database()

    print("\n" + "=" * 60)
    print("DATABASE CLEANUP")
    print("=" * 60)

    if args.review:
        # Show videos that would be affected by cleanup
        min_confidence = args.min_confidence or STORAGE_CONFIG.get("min_storage_confidence", 0.50)

        print(f"\nAnalyzing videos with confidence < {min_confidence}...")
        print("-" * 60)

        df = db.get_all_sermons()

        if df.empty:
            print("No videos in database.")
            return

        # Filter low confidence videos
        low_conf = df[df["confidence_score"] < min_confidence]
        unknown = df[df["content_type"] == "UNKNOWN"]
        music_low = df[(df["content_type"] == "MUSIC") & (df["confidence_score"] < 0.70)]

        print(f"\nCleanup candidates:")
        print(f"  Videos with confidence < {min_confidence}: {len(low_conf)}")
        print(f"  UNKNOWN content type: {len(unknown)}")
        print(f"  Low-confidence MUSIC: {len(music_low)}")

        # Show details
        if len(low_conf) > 0:
            print(f"\n--- Sample low-confidence videos (top 10) ---")
            display_data = []
            for _, row in low_conf.head(10).iterrows():
                display_data.append([
                    row["video_id"],
                    row["title"][:40] + "..." if len(str(row["title"])) > 40 else row["title"],
                    row["channel_name"][:20] if row.get("channel_name") else "Unknown",
                    row["content_type"],
                    f"{row['confidence_score']:.2f}",
                ])
            headers = ["Video ID", "Title", "Channel", "Type", "Conf"]
            print(tabulate(display_data, headers=headers, tablefmt="simple"))

        print(f"\nTo purge these videos, run:")
        print(f"  python main.py cleanup --purge --min-confidence {min_confidence}")

    elif args.purge:
        # Delete low confidence videos
        min_confidence = args.min_confidence or STORAGE_CONFIG.get("min_storage_confidence", 0.50)

        print(f"\nPurging videos with confidence < {min_confidence}...")

        if not args.force:
            confirm = input(f"\nThis will DELETE videos. Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                return

        # Get count before deletion
        df = db.get_all_sermons()
        low_conf = df[df["confidence_score"] < min_confidence]
        count_to_delete = len(low_conf)

        if count_to_delete == 0:
            print(f"No videos with confidence < {min_confidence} found.")
            return

        # Delete videos
        deleted = db.delete_low_confidence_videos(min_confidence)
        print(f"\n[OK] Deleted {deleted} videos with confidence < {min_confidence}")

    elif args.reclassify:
        # Re-run classification on all videos
        print("\nRe-classifying all videos with updated rules...")
        print("-" * 60)

        if not args.force:
            confirm = input("\nThis will re-classify ALL videos. Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                return

        # Get all videos
        df = db.get_all_sermons()

        if df.empty:
            print("No videos in database.")
            return

        print(f"Processing {len(df)} videos...")

        classifier = ContentClassifier()
        reclassified = 0
        changed = 0

        for _, row in df.iterrows():
            from models import VideoMetadata
            video = VideoMetadata.from_dict(row.to_dict())
            old_type = video.content_type
            old_conf = video.confidence_score

            # Re-classify
            video = classifier.classify(video)

            # Update if changed
            if video.content_type != old_type or abs(video.confidence_score - old_conf) > 0.1:
                db.update_video_classification(
                    video_id=video.video_id,
                    content_type=video.content_type,
                    confidence_score=video.confidence_score,
                    needs_review=video.needs_review,
                    identity_matched=getattr(video, 'identity_matched', False),
                    channel_trust_level=getattr(video, 'channel_trust_level', 0)
                )
                changed += 1

            reclassified += 1
            if reclassified % 50 == 0:
                print(f"  Processed {reclassified}/{len(df)} videos...")

        print(f"\n[OK] Re-classified {reclassified} videos")
        print(f"     {changed} videos had classification changes")

    else:
        print("\nUsage:")
        print("  python main.py cleanup --review              Review low-confidence videos")
        print("  python main.py cleanup --purge               Delete low-confidence videos")
        print("  python main.py cleanup --reclassify          Re-run classification on all videos")
        print("\nOptions:")
        print("  --min-confidence 0.50   Set confidence threshold")
        print("  --force                 Skip confirmation prompts")

    print("=" * 60 + "\n")


def cmd_verify_faces(args):
    """Run face verification on videos in the database."""
    from classifier import ContentClassifier, PHOTOS_DIR
    from models import ContentType

    db = Database()

    print("\n" + "=" * 60)
    print("FACE VERIFICATION PIPELINE")
    print("=" * 60)

    # Get face verification stats first
    stats = db.get_face_verification_stats()
    print(f"\nDatabase status:")
    print(f"  Total videos:      {stats['total_videos']}")
    print(f"  Already verified:  {stats['face_verified']}")
    print(f"  Not yet verified:  {stats['not_verified']}")

    # Get videos to verify
    channel_filter = args.channel if hasattr(args, 'channel') else None
    limit = args.limit if hasattr(args, 'limit') else None

    videos = db.get_videos_for_face_verification(
        only_unverified=not args.all,
        channel_filter=channel_filter,
        limit=limit
    )

    if not videos:
        print("\nNo videos to verify.")
        print("=" * 60 + "\n")
        return

    print(f"\nVerifying {len(videos)} videos...")
    print(f"Photos directory: {PHOTOS_DIR}")
    print("-" * 60)

    # Initialize classifier for face recognition
    classifier = ContentClassifier(use_frame_extraction=args.frames)

    if classifier.face_recognizer is None:
        print("\n[!!] Face recognition not available!")
        print("   Make sure DeepFace/TensorFlow is installed (requires Python 3.11/3.12)")
        print("   Currently using OpenCV fallback (detection only, no recognition)")
        print("=" * 60 + "\n")
        return

    verified_count = 0
    not_verified_count = 0
    errors = []

    for i, video in enumerate(videos, 1):
        # Encode title safely for console output
        safe_title = video.title[:50].encode('ascii', 'replace').decode('ascii')
        safe_channel = (video.channel_name or "Unknown").encode('ascii', 'replace').decode('ascii')
        print(f"\n[{i}/{len(videos)}] {safe_title}...")
        print(f"         Channel: {safe_channel}")

        try:
            # Run face verification
            face_verified, confidence = classifier._verify_face(video)

            if face_verified:
                print(f"         [OK] VERIFIED (confidence: {confidence:.2f})")
                verified_count += 1

                # Update database
                db.update_face_verification(
                    video_id=video.video_id,
                    face_verified=True,
                    confidence_score=confidence,
                    content_type=ContentType.PREACHING,
                    needs_review=False
                )
            else:
                print(f"         [--] NOT VERIFIED (confidence: {confidence:.2f})")
                not_verified_count += 1

                # Update database - flag for review if from strict channel
                is_strict = classifier._is_strict_channel(video.channel_name)
                db.update_face_verification(
                    video_id=video.video_id,
                    face_verified=False,
                    confidence_score=confidence,
                    content_type=ContentType.UNKNOWN if is_strict else video.content_type,
                    needs_review=is_strict
                )

        except Exception as e:
            print(f"         [!!] Error: {e}")
            errors.append(f"{video.video_id}: {e}")

    # Print summary
    print("\n" + "-" * 60)
    print("VERIFICATION SUMMARY")
    print("-" * 60)
    print(f"Videos processed:     {len(videos)}")
    print(f"Face verified:        {verified_count}")
    print(f"Not verified:         {not_verified_count}")
    print(f"Errors:               {len(errors)}")

    if errors:
        print("\nErrors encountered:")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    print("=" * 60 + "\n")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_duration(seconds) -> str:
    """Format duration in seconds to HH:MM:SS."""
    if seconds is None:
        return "Unknown"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_date(date_str) -> str:
    """Format YYYYMMDD to YYYY-MM-DD."""
    if date_str and len(str(date_str)) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return str(date_str) if date_str else "Unknown"


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ministry Video Fetcher - Track preaching videos of Apostle Narcisse Majila",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py fetch                    Run fetch from YouTube (default)
  python main.py fetch --facebook         Run fetch from Facebook only
  python main.py fetch --all              Run fetch from all platforms
  python main.py fetch -p facebook        Same as --facebook
  python main.py stats                    Show database statistics
  python main.py review                   List videos needing review
  python main.py export                   Export to CSV
  python main.py sample                   Show sample videos
  python main.py channels                 Show channel breakdown
  python main.py mark VIDEO_ID PREACHING  Mark video as reviewed
  python main.py verify-faces             Run face verification on all unverified videos
  python main.py verify-faces --limit 10  Verify only 10 videos
  python main.py verify-faces --channel "Ramah"  Verify videos from Ramah channel
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Fetch command
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Run fetch from video sources",
        description="Fetch videos from YouTube and/or Facebook"
    )
    fetch_parser.add_argument(
        "--platform", "-p",
        choices=["youtube", "facebook", "all"],
        default="youtube",
        help="Platform to fetch from (default: youtube)"
    )
    fetch_parser.add_argument(
        "--youtube", "-y",
        action="store_const",
        const="youtube",
        dest="platform",
        help="Fetch from YouTube only (default)"
    )
    fetch_parser.add_argument(
        "--facebook", "-f",
        action="store_const",
        const="facebook",
        dest="platform",
        help="Fetch from Facebook only"
    )
    fetch_parser.add_argument(
        "--all", "-a",
        action="store_const",
        const="all",
        dest="platform",
        help="Fetch from all platforms (YouTube and Facebook)"
    )
    fetch_parser.set_defaults(func=cmd_fetch)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show database statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # Review command
    review_parser = subparsers.add_parser("review", help="List videos flagged for review")
    review_parser.set_defaults(func=cmd_review)

    # Export command
    export_parser = subparsers.add_parser("export", help="Export to CSV")
    export_parser.add_argument("-o", "--output", help="Output file path")
    export_parser.set_defaults(func=cmd_export)

    # Sample command
    sample_parser = subparsers.add_parser("sample", help="Show sample videos")
    sample_parser.set_defaults(func=cmd_sample)

    # Channels command
    channels_parser = subparsers.add_parser("channels", help="Show channel breakdown")
    channels_parser.set_defaults(func=cmd_channels)

    # Mark reviewed command
    mark_parser = subparsers.add_parser("mark", help="Mark video as reviewed")
    mark_parser.add_argument("video_id", help="YouTube video ID")
    mark_parser.add_argument(
        "content_type",
        choices=["PREACHING", "MUSIC", "UNKNOWN"],
        help="Correct content type"
    )
    mark_parser.set_defaults(func=cmd_mark_reviewed)

    # Cleanup shorts command
    cleanup_shorts_parser = subparsers.add_parser("cleanup-shorts", help="Delete videos shorter than 10 minutes")
    cleanup_shorts_parser.set_defaults(func=cmd_cleanup_shorts)

    # Cleanup command (new - for reviewing/purging low-confidence videos)
    cleanup_parser = subparsers.add_parser(
        "cleanup",
        help="Review, purge, or reclassify videos",
        description="Clean up database by reviewing or removing low-confidence videos"
    )
    cleanup_parser.add_argument(
        "--review", "-r",
        action="store_true",
        help="Review videos that would be affected by cleanup"
    )
    cleanup_parser.add_argument(
        "--purge", "-p",
        action="store_true",
        help="Delete videos below confidence threshold"
    )
    cleanup_parser.add_argument(
        "--reclassify",
        action="store_true",
        help="Re-run classification on all videos with updated rules"
    )
    cleanup_parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.50,
        help="Minimum confidence threshold (default: 0.50)"
    )
    cleanup_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompts"
    )
    cleanup_parser.set_defaults(func=cmd_cleanup)

    # Verify faces command
    verify_parser = subparsers.add_parser("verify-faces", help="Run face verification on videos")
    verify_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Verify all videos, not just unverified ones"
    )
    verify_parser.add_argument(
        "--channel", "-c",
        help="Filter by channel name"
    )
    verify_parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Maximum number of videos to verify"
    )
    verify_parser.add_argument(
        "--frames", "-f",
        action="store_true",
        default=True,
        help="Enable video frame extraction for deeper analysis (default: True)"
    )
    verify_parser.add_argument(
        "--no-frames",
        action="store_false",
        dest="frames",
        help="Disable video frame extraction (faster, thumbnail only)"
    )
    verify_parser.set_defaults(func=cmd_verify_faces)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
