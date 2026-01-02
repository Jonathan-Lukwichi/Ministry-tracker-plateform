# Ministry Video Fetcher

A Python tool to fetch, classify, and track preaching videos of **Apostle Narcisse Majila** from YouTube. This prototype automatically collects video metadata from multiple YouTube channels, classifies content as preaching or music, and stores results in a SQLite database.

## Features

- **Multi-source fetching**: Searches YouTube with multiple queries and fetches from the primary church channel
- **Smart classification**: Distinguishes preaching content from music using keyword analysis and duration heuristics
- **Language detection**: Identifies French vs English content
- **Deduplication**: Tracks videos by ID to avoid duplicates across searches
- **Review flagging**: Flags uncertain classifications for manual review
- **Export capability**: Export data to CSV for analysis

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd ministry_video_fetcher
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Fetch Videos

Run a complete fetch from all sources:

```bash
python main.py fetch
```

This will:
1. Fetch all videos from Ramah Full Gospel Church Pretoria channel
2. Run 13 different search queries
3. Classify each video (PREACHING, MUSIC, or UNKNOWN)
4. Store results in `ministry_videos.db`
5. Print a detailed summary

### View Statistics

```bash
python main.py stats
```

Shows:
- Total videos in database
- Breakdown by content type
- Breakdown by language
- Videos needing review
- Unique channels
- Date range
- Total preaching hours
- Top 10 channels

### Review Queue

List videos that need manual review:

```bash
python main.py review
```

### Export to CSV

```bash
python main.py export
# or specify output file
python main.py export -o my_export.csv
```

### View Sample Videos

```bash
python main.py sample
```

### Show Channel Breakdown

```bash
python main.py channels
```

### Mark Video as Reviewed

Manually correct a video's classification:

```bash
python main.py mark VIDEO_ID PREACHING
python main.py mark VIDEO_ID MUSIC
```

## Project Structure

```
ministry_video_fetcher/
├── config.py           # Search queries, keywords, classification rules
├── models.py           # Data classes (VideoMetadata, FetchLog, etc.)
├── database.py         # SQLite database operations
├── classifier.py       # Preaching vs Music classification logic
├── fetcher.py          # yt-dlp fetching implementation
├── main.py             # CLI entry point
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Configuration

Edit `config.py` to customize:

- **Search queries**: Add/modify search terms
- **Classification keywords**: Add preaching/music indicators
- **Duration thresholds**: Adjust sermon length heuristics
- **Rate limiting**: Change request delays

## Classification Logic

Videos are classified based on:

1. **Title/description keywords**:
   - PREACHING: sermon, predication, message, deliverance, faith, healing...
   - MUSIC: music, song, album, clip officiel, feat., lyrics...

2. **Duration analysis**:
   - < 3 min: Likely music
   - 3-8 min: Uncertain
   - 15+ min: Likely preaching
   - 20+ min: Very likely preaching

3. **Confidence scoring**: 0.0 to 1.0
   - Videos with confidence < 0.6 are flagged for review

## Database Schema

### videos table
| Column | Type | Description |
|--------|------|-------------|
| video_id | TEXT | YouTube video ID (primary key) |
| title | TEXT | Video title |
| description | TEXT | First 500 chars of description |
| duration | INTEGER | Duration in seconds |
| upload_date | TEXT | YYYYMMDD format |
| view_count | INTEGER | Number of views |
| like_count | INTEGER | Number of likes |
| thumbnail_url | TEXT | Thumbnail URL |
| channel_name | TEXT | Uploading channel name |
| channel_id | TEXT | YouTube channel ID |
| channel_url | TEXT | Channel URL |
| video_url | TEXT | Full video URL |
| content_type | TEXT | PREACHING, MUSIC, or UNKNOWN |
| confidence_score | REAL | Classification confidence (0-1) |
| needs_review | INTEGER | 1 if needs manual review |
| language_detected | TEXT | FR, EN, or UNKNOWN |
| fetched_at | TEXT | ISO timestamp |
| search_query_used | TEXT | Query that found this video |

### fetch_logs table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment ID |
| fetch_timestamp | TEXT | When fetch occurred |
| query_used | TEXT | Search query or channel |
| videos_found | INTEGER | Total found |
| videos_added | INTEGER | New videos added |
| videos_skipped | INTEGER | Duplicates skipped |
| music_excluded | INTEGER | Music videos excluded |
| errors_count | INTEGER | Errors encountered |

## Programmatic Usage

```python
from database import Database
from fetcher import VideoFetcher

# Initialize
db = Database()
fetcher = VideoFetcher(db)

# Run fetch
summary = fetcher.fetch_all()
summary.print_summary()

# Query data
df = db.get_all_sermons()
print(f"Total sermons: {len(df)}")

# Get by channel
ramah_sermons = db.get_sermons_by_channel("Ramah")

# Get by year
sermons_2024 = db.get_sermons_by_year(2024)

# Get French sermons
french = db.get_sermons_by_language("FR")

# Get total hours
hours = db.get_total_preaching_hours()
print(f"Total preaching hours: {hours:.1f}")

# Mark as reviewed
from models import ContentType
db.mark_as_reviewed("abc123", ContentType.PREACHING)
```

## Notes

- **Rate limiting**: The fetcher waits 1 second between requests to avoid being blocked
- **No API keys**: Uses yt-dlp which doesn't require YouTube API credentials
- **Errors**: Network errors are logged and skipped; the fetcher continues with remaining videos
- **Duplicates**: Videos are tracked by ID; re-running fetch won't create duplicates

## License

MIT License - Free for personal and commercial use.
