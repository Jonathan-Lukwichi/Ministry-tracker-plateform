"""
FastAPI server for Ministry Video API.

Run with: uvicorn api:app --reload --port 8000
"""

import sys
import os
# Add the current directory to the path to find local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import base64
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
from database import Database

# Import face recognition
try:
    from face_recognition import get_face_recognizer
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Import forecasting
try:
    from forecasting import MinistryForecaster, XGBOOST_AVAILABLE
    forecaster = MinistryForecaster()
except ImportError:
    XGBOOST_AVAILABLE = False
    forecaster = None

# Import health insights
try:
    from health_insights import HealthInsightsEngine
    from ollama_service import ollama_service
    HEALTH_AVAILABLE = True
except ImportError:
    HEALTH_AVAILABLE = False
    ollama_service = None

# Import planning engine
try:
    from planning_engine import PlanningEngine
    PLANNING_AVAILABLE = True
except ImportError:
    PLANNING_AVAILABLE = False

from math import radians, sin, cos, sqrt, atan2

# Photos directory - relative to parent directory
PHOTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "photos")

# Helper to get face recognizer with correct path
def get_recognizer():
    return get_face_recognizer(photos_dir=PHOTOS_DIR)

app = FastAPI(title="Ministry Video API", version="1.0.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database instance
db = Database()


@app.get("/api/stats")
def get_stats():
    """Get video statistics from database."""
    stats = db.get_statistics()

    # Format for frontend
    return {
        "total_videos": stats.get("total_videos", 0),
        "by_content_type": stats.get("by_content_type", {}),
        "by_language": stats.get("by_language", {}),
        "needs_review": stats.get("needs_review", 0),
        "unique_channels": stats.get("unique_channels", 0),
        "total_preaching_hours": round(stats.get("total_hours", 0), 1),
        "oldest_video": stats.get("oldest_video"),
        "newest_video": stats.get("newest_video"),
        "top_channels": [
            {"name": name or "Unknown", "count": count}
            for name, count in stats.get("top_channels", [])[:5]
        ],
    }


@app.get("/api/videos")
def get_videos(
    limit: int = 100,
    year: int = None,
    month: int = None,
    channel: str = None,
    place: str = None,
):
    """Get videos with optional filters."""
    df = db.get_all_sermons()

    # Apply year filter
    if year and "upload_date" in df.columns:
        df = df[df["upload_date"].astype(str).str[:4] == str(year)]

    # Apply month filter (requires year)
    if month and year and "upload_date" in df.columns:
        month_str = f"{year}{str(month).zfill(2)}"
        df = df[df["upload_date"].astype(str).str[:6] == month_str]

    # Apply channel filter
    if channel and "channel_name" in df.columns:
        df = df[df["channel_name"].str.contains(channel, case=False, na=False)]

    # Apply place filter
    if place:
        # Known locations to extract from channel names and titles
        known_places = {
            "Pretoria": ["pretoria", "pta"],
            "Kinshasa": ["kinshasa", "rdc", "drc"],
            "Lubumbashi": ["lubumbashi"],
            "Likasi": ["likasi"],
            "Paris": ["paris", "france"],
            "London": ["london", "uk", "england"],
            "Brussels": ["brussels", "bruxelles", "belgium", "belgique"],
            "Johannesburg": ["johannesburg", "joburg", "jhb"],
            "Cape Town": ["cape town", "capetown"],
            "Durban": ["durban"],
        }

        def matches_place(row, target_place):
            text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
            if target_place == "Other":
                # Check if it doesn't match any known place
                for keywords in known_places.values():
                    for keyword in keywords:
                        if keyword in text:
                            return False
                return True
            else:
                keywords = known_places.get(target_place, [])
                for keyword in keywords:
                    if keyword in text:
                        return True
                return False

        df = df[df.apply(lambda row: matches_place(row, place), axis=1)]

    videos = []
    for _, row in df.head(limit).iterrows():
        videos.append({
            "video_id": row["video_id"],
            "title": row["title"],
            "channel_name": row["channel_name"],
            "duration": row["duration"],
            "upload_date": row["upload_date"],
            "view_count": row["view_count"],
            "content_type": row["content_type"],
            "language": row["language_detected"],
            "video_url": row["video_url"],
            "thumbnail_url": row["thumbnail_url"],
        })

    return {"videos": videos, "total": len(df)}


@app.get("/api/videos/by-year")
def get_videos_by_year():
    """Get videos grouped by year."""
    df = db.get_all_sermons()

    if df.empty:
        return {"years": []}

    # Extract year from upload_date
    df["year"] = df["upload_date"].astype(str).str[:4]

    # Group by year
    year_counts = df.groupby("year").agg({
        "video_id": "count",
        "duration": "sum"
    }).reset_index()

    years = []
    for _, row in year_counts.sort_values("year", ascending=False).iterrows():
        if row["year"] and row["year"] != "None" and len(row["year"]) == 4:
            years.append({
                "year": row["year"],
                "count": int(row["video_id"]),
                "total_duration": int(row["duration"]) if row["duration"] else 0
            })

    return {"years": years}


@app.get("/api/videos/by-month")
def get_videos_by_month(year: int = None):
    """Get videos grouped by month."""
    df = db.get_all_sermons()

    if df.empty:
        return {"months": []}

    # Extract year and month
    df["year"] = df["upload_date"].astype(str).str[:4]
    df["month"] = df["upload_date"].astype(str).str[4:6]
    df["year_month"] = df["upload_date"].astype(str).str[:6]

    # Filter by year if provided
    if year:
        df = df[df["year"] == str(year)]

    # Group by month
    month_counts = df.groupby(["year", "month", "year_month"]).agg({
        "video_id": "count",
        "duration": "sum"
    }).reset_index()

    months = []
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for _, row in month_counts.sort_values("year_month", ascending=False).iterrows():
        if row["month"] and row["month"].isdigit():
            month_num = int(row["month"])
            if 1 <= month_num <= 12:
                months.append({
                    "year": row["year"],
                    "month": month_num,
                    "month_name": month_names[month_num],
                    "year_month": row["year_month"],
                    "count": int(row["video_id"]),
                    "total_duration": int(row["duration"]) if row["duration"] else 0
                })

    return {"months": months}


@app.get("/api/videos/by-channel")
def get_videos_by_channel():
    """Get videos grouped by channel."""
    channels = db.get_channel_breakdown()

    return {
        "channels": [
            {"name": name or "Unknown", "count": count}
            for name, count in channels
        ]
    }


@app.get("/api/videos/by-place")
def get_videos_by_place():
    """Get videos grouped by place/location."""
    df = db.get_all_sermons()

    if df.empty:
        return {"places": []}

    # Known locations to extract from channel names and titles
    known_places = {
        "Pretoria": ["pretoria", "pta"],
        "Kinshasa": ["kinshasa", "rdc", "drc"],
        "Lubumbashi": ["lubumbashi"],
        "Likasi": ["likasi"],
        "Paris": ["paris", "france"],
        "London": ["london", "uk", "england"],
        "Brussels": ["brussels", "bruxelles", "belgium", "belgique"],
        "Johannesburg": ["johannesburg", "joburg", "jhb"],
        "Cape Town": ["cape town", "capetown"],
        "Durban": ["durban"],
    }

    def extract_place(row):
        """Extract place from channel name and title."""
        text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()

        for place, keywords in known_places.items():
            for keyword in keywords:
                if keyword in text:
                    return place

        # Default to "Other" for unknown locations
        return "Other"

    # Extract place for each video
    df["place"] = df.apply(extract_place, axis=1)

    # Group by place
    place_counts = df.groupby("place").agg({
        "video_id": "count",
        "duration": "sum"
    }).reset_index()

    places = []
    for _, row in place_counts.sort_values("video_id", ascending=False).iterrows():
        places.append({
            "name": row["place"],
            "count": int(row["video_id"]),
            "total_duration": int(row["duration"]) if row["duration"] else 0
        })

    return {"places": places}


@app.get("/api/videos/recent-weeks")
def get_videos_recent_weeks():
    """Get videos from recent weeks."""
    from datetime import datetime, timedelta

    df = db.get_all_sermons()

    if df.empty:
        return {"weeks": []}

    # Convert upload_date to datetime
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])

    # Get current date
    today = datetime.now()

    weeks = []
    for i in range(12):  # Last 12 weeks
        week_start = today - timedelta(days=today.weekday() + 7 * i)
        week_end = week_start + timedelta(days=6)

        week_df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]

        if len(week_df) > 0 or i < 4:  # Always show last 4 weeks
            weeks.append({
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "week_label": f"Week of {week_start.strftime('%b %d')}",
                "count": len(week_df),
                "total_duration": int(week_df["duration"].sum()) if len(week_df) > 0 else 0
            })

    return {"weeks": weeks}


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@app.get("/api/analytics/summary")
def get_analytics_summary():
    """Get KPI summary with trends for analytics dashboard."""
    from datetime import datetime, timedelta

    df = db.get_all_sermons()

    if df.empty:
        return {
            "totalSermons": 0,
            "totalHours": 0,
            "avgDuration": 0,
            "totalViews": 0,
            "trends": {"sermonsChange": 0, "hoursChange": 0, "durationChange": 0, "viewsChange": 0}
        }

    # Current totals
    total_sermons = len(df)
    total_duration = df["duration"].sum() if "duration" in df.columns else 0
    total_hours = total_duration / 3600 if total_duration else 0
    avg_duration = total_duration / total_sermons if total_sermons > 0 else 0
    total_views = df["view_count"].sum() if "view_count" in df.columns else 0

    # Calculate trends (compare current year vs previous year)
    current_year = datetime.now().year
    previous_year = current_year - 1

    df["year"] = df["upload_date"].astype(str).str[:4]

    current_df = df[df["year"] == str(current_year)]
    previous_df = df[df["year"] == str(previous_year)]

    def calc_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)

    trends = {
        "sermonsChange": calc_change(len(current_df), len(previous_df)),
        "hoursChange": calc_change(
            current_df["duration"].sum() / 3600 if len(current_df) > 0 else 0,
            previous_df["duration"].sum() / 3600 if len(previous_df) > 0 else 0
        ),
        "durationChange": calc_change(
            current_df["duration"].mean() if len(current_df) > 0 else 0,
            previous_df["duration"].mean() if len(previous_df) > 0 else 0
        ),
        "viewsChange": calc_change(
            current_df["view_count"].sum() if len(current_df) > 0 else 0,
            previous_df["view_count"].sum() if len(previous_df) > 0 else 0
        ),
    }

    return {
        "summary": {
            "totalSermons": total_sermons,
            "totalHours": round(total_hours, 1),
            "avgDuration": round(avg_duration / 60, 1),  # In minutes
            "totalViews": int(total_views) if total_views else 0,
            "trends": trends
        }
    }


@app.get("/api/analytics/sermons-by-period")
def get_sermons_by_period(period: str = "year"):
    """Get sermon counts by time period (year, month, week)."""
    from datetime import datetime, timedelta

    df = db.get_all_sermons()

    if df.empty:
        return {"data": [], "period": period}

    # Parse upload_date
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])

    if period == "year":
        df["period"] = df["date"].dt.year.astype(str)
        grouped = df.groupby("period").agg({
            "video_id": "count",
            "duration": "sum"
        }).reset_index()
        data = [
            {
                "period": str(row["period"]),
                "value": int(row["video_id"])
            }
            for _, row in grouped.sort_values("period").iterrows()
        ]

    elif period == "month":
        # Last 24 months
        df["period"] = df["date"].dt.strftime("%Y-%m")
        grouped = df.groupby("period").agg({
            "video_id": "count",
            "duration": "sum"
        }).reset_index()
        data = [
            {
                "period": row["period"],
                "value": int(row["video_id"])
            }
            for _, row in grouped.sort_values("period").tail(24).iterrows()
        ]

    elif period == "week":
        # Last 12 weeks
        today = datetime.now()
        data = []
        for i in range(11, -1, -1):
            week_start = today - timedelta(days=today.weekday() + 7 * i)
            week_end = week_start + timedelta(days=6)
            week_df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]
            data.append({
                "period": f"W{12-i}",
                "value": len(week_df)
            })

    else:
        return {"data": [], "period": period, "error": "Invalid period"}

    return {"data": data, "period": period}


@app.get("/api/analytics/duration-by-period")
def get_duration_by_period(period: str = "year"):
    """Get average duration by time period."""
    from datetime import datetime, timedelta

    df = db.get_all_sermons()

    if df.empty:
        return {"data": [], "period": period}

    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])

    if period == "year":
        df["period"] = df["date"].dt.year.astype(str)
        grouped = df.groupby("period").agg({
            "duration": ["mean", "sum", "count"]
        }).reset_index()
        grouped.columns = ["period", "avgDuration", "totalDuration", "count"]
        data = [
            {
                "period": str(row["period"]),
                "value": round(row["avgDuration"] / 3600, 2)
            }
            for _, row in grouped.sort_values("period").iterrows()
        ]

    elif period == "month":
        df["period"] = df["date"].dt.strftime("%Y-%m")
        grouped = df.groupby("period").agg({
            "duration": ["mean", "sum", "count"]
        }).reset_index()
        grouped.columns = ["period", "avgDuration", "totalDuration", "count"]
        data = [
            {
                "period": row["period"],
                "value": round(row["avgDuration"] / 3600, 2)
            }
            for _, row in grouped.sort_values("period").tail(24).iterrows()
        ]

    elif period == "week":
        today = datetime.now()
        data = []
        for i in range(11, -1, -1):
            week_start = today - timedelta(days=today.weekday() + 7 * i)
            week_end = week_start + timedelta(days=6)
            week_df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]
            data.append({
                "period": f"W{12-i}",
                "value": round(week_df["duration"].sum() / 3600, 1) if len(week_df) > 0 else 0
            })

    else:
        return {"data": [], "period": period, "error": "Invalid period"}

    return {"data": data, "period": period}


@app.get("/api/analytics/views-by-period")
def get_views_by_period(period: str = "year"):
    """Get view statistics by time period."""
    from datetime import datetime, timedelta

    df = db.get_all_sermons()

    if df.empty:
        return {"data": [], "period": period}

    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])

    # Ensure view_count is numeric
    df["view_count"] = df["view_count"].fillna(0).astype(int)

    if period == "year":
        df["period"] = df["date"].dt.year.astype(str)
        grouped = df.groupby("period").agg({
            "view_count": ["mean", "sum", "count"]
        }).reset_index()
        grouped.columns = ["period", "avgViews", "totalViews", "count"]
        data = [
            {
                "period": str(row["period"]),
                "value": int(row["avgViews"])
            }
            for _, row in grouped.sort_values("period").iterrows()
        ]

    elif period == "month":
        df["period"] = df["date"].dt.strftime("%Y-%m")
        grouped = df.groupby("period").agg({
            "view_count": ["mean", "sum", "count"]
        }).reset_index()
        grouped.columns = ["period", "avgViews", "totalViews", "count"]
        data = [
            {
                "period": row["period"],
                "value": int(row["avgViews"])
            }
            for _, row in grouped.sort_values("period").tail(24).iterrows()
        ]

    elif period == "week":
        today = datetime.now()
        data = []
        for i in range(11, -1, -1):
            week_start = today - timedelta(days=today.weekday() + 7 * i)
            week_end = week_start + timedelta(days=6)
            week_df = df[(df["date"] >= week_start) & (df["date"] <= week_end)]
            data.append({
                "period": f"W{12-i}",
                "value": int(week_df["view_count"].mean()) if len(week_df) > 0 else 0
            })

    else:
        return {"data": [], "period": period, "error": "Invalid period"}

    return {"data": data, "period": period}


# =============================================================================
# PIE CHART & HISTOGRAM ANALYTICS ENDPOINTS
# =============================================================================

@app.get("/api/analytics/year-distribution")
def get_year_distribution():
    """Get sermon counts per year for pie chart visualization."""
    df = db.get_all_sermons()

    if df.empty:
        return {"data": [], "busiestYear": None, "totalSermons": 0}

    # Extract year from upload_date
    df["year"] = df["upload_date"].astype(str).str[:4]

    # Group by year
    grouped = df.groupby("year").size().reset_index(name="value")
    total = grouped["value"].sum()

    # Calculate percentages and format data
    data = []
    for _, row in grouped.sort_values("value", ascending=False).iterrows():
        data.append({
            "year": row["year"],
            "value": int(row["value"]),
            "percentage": round((row["value"] / total) * 100, 1)
        })

    # Find busiest year
    busiest_year = data[0]["year"] if data else None

    return {
        "data": data,
        "busiestYear": busiest_year,
        "totalSermons": int(total)
    }


@app.get("/api/analytics/months-by-year")
def get_months_by_year(year: int = 2025):
    """Get monthly breakdown for a specific year (for dynamic pie chart)."""
    from datetime import datetime

    df = db.get_all_sermons()

    if df.empty:
        return {"data": [], "year": year, "busiestMonth": None}

    # Parse dates and filter by year
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Filter to selected year
    year_df = df[df["year"] == year]

    if year_df.empty:
        return {"data": [], "year": year, "busiestMonth": None}

    # Group by month
    grouped = year_df.groupby("month").size().reset_index(name="value")

    # Month names
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Build data with all 12 months (0 for missing)
    data = []
    for m in range(1, 13):
        month_data = grouped[grouped["month"] == m]
        value = int(month_data["value"].iloc[0]) if len(month_data) > 0 else 0
        data.append({
            "month": month_names[m - 1],
            "monthNum": m,
            "value": value
        })

    # Find busiest month
    max_value = max(d["value"] for d in data)
    busiest_month = next((d["month"] for d in data if d["value"] == max_value), None)

    return {
        "data": data,
        "year": year,
        "busiestMonth": busiest_month,
        "totalSermons": sum(d["value"] for d in data)
    }


@app.get("/api/analytics/busiest-months")
def get_busiest_months():
    """Get aggregated sermon counts by month across ALL years (for histogram)."""
    from datetime import datetime

    df = db.get_all_sermons()

    if df.empty:
        return {"data": []}

    # Parse dates
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year

    # Group by month (across all years)
    grouped = df.groupby("month").size().reset_index(name="total")

    # Calculate number of years with data
    years_count = df["year"].nunique()

    # Month names
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Build data for all 12 months
    data = []
    for m in range(1, 13):
        month_data = grouped[grouped["month"] == m]
        total = int(month_data["total"].iloc[0]) if len(month_data) > 0 else 0
        data.append({
            "month": month_names[m - 1],
            "monthNum": m,
            "total": total,
            "average": round(total / years_count, 1) if years_count > 0 else 0
        })

    return {"data": data}


@app.get("/api/analytics/year-summary")
def get_year_summary(year: int = 2025):
    """Get KPIs for a specific year (for 2025 analysis tab)."""
    from datetime import datetime

    df = db.get_all_sermons()

    if df.empty:
        return {
            "year": year,
            "totalSermons": 0,
            "totalHours": 0,
            "avgDuration": 0,
            "totalViews": 0,
            "busiestMonth": None,
            "trends": {"sermonsChange": 0, "hoursChange": 0, "viewsChange": 0}
        }

    # Parse dates
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])
    df["year_num"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Filter to selected year and previous year
    year_df = df[df["year_num"] == year]
    prev_year_df = df[df["year_num"] == year - 1]

    # Calculate current year metrics
    total_sermons = len(year_df)
    total_duration = year_df["duration"].sum() if "duration" in year_df.columns and len(year_df) > 0 else 0
    total_hours = total_duration / 3600 if total_duration else 0
    avg_duration = (total_duration / total_sermons / 60) if total_sermons > 0 else 0  # in minutes
    total_views = int(year_df["view_count"].sum()) if "view_count" in year_df.columns and len(year_df) > 0 else 0

    # Find busiest month
    busiest_month = None
    if len(year_df) > 0:
        month_counts = year_df.groupby("month").size()
        if len(month_counts) > 0:
            busiest_month_num = month_counts.idxmax()
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            busiest_month = month_names[busiest_month_num - 1]

    # Calculate trends vs previous year
    def calc_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)

    prev_sermons = len(prev_year_df)
    prev_hours = prev_year_df["duration"].sum() / 3600 if "duration" in prev_year_df.columns and len(prev_year_df) > 0 else 0
    prev_views = int(prev_year_df["view_count"].sum()) if "view_count" in prev_year_df.columns and len(prev_year_df) > 0 else 0

    trends = {
        "sermonsChange": calc_change(total_sermons, prev_sermons),
        "hoursChange": calc_change(total_hours, prev_hours),
        "viewsChange": calc_change(total_views, prev_views)
    }

    return {
        "year": year,
        "totalSermons": total_sermons,
        "totalHours": round(total_hours, 1),
        "avgDuration": round(avg_duration, 1),
        "totalViews": total_views,
        "busiestMonth": busiest_month,
        "trends": trends
    }


# =============================================================================
# FACE RECOGNITION / PHOTO MANAGEMENT ENDPOINTS
# =============================================================================

class FaceTestRequest(BaseModel):
    video_url: str
    thumbnail_url: Optional[str] = None


@app.get("/api/reference-photos")
def get_reference_photos():
    """Get list of reference photos for face recognition."""
    if not FACE_RECOGNITION_AVAILABLE:
        return {"photos": [], "available": False, "error": "Face recognition not available"}

    try:
        recognizer = get_recognizer()
        photos = recognizer.get_reference_photos()

        # Add base64 encoded thumbnails for display
        photos_with_data = []
        for photo in photos:
            photo_data = {
                "filename": photo["filename"],
                "size": photo["size"],
            }
            # Read and encode small preview
            try:
                with open(photo["path"], "rb") as f:
                    image_data = f.read()
                    photo_data["data"] = base64.b64encode(image_data).decode("utf-8")
                    # Determine mime type
                    ext = photo["filename"].lower().split(".")[-1]
                    mime_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
                    photo_data["mime_type"] = mime_types.get(ext, "image/jpeg")
            except Exception:
                photo_data["data"] = None
                photo_data["mime_type"] = None

            photos_with_data.append(photo_data)

        return {
            "photos": photos_with_data,
            "available": True,
            "model_loaded": recognizer.model_loaded,
        }

    except Exception as e:
        return {"photos": [], "available": False, "error": str(e)}


@app.post("/api/reference-photos")
async def upload_reference_photo(file: UploadFile = File(...)):
    """Upload a new reference photo."""
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Face recognition not available")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are allowed")

    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    try:
        recognizer = get_recognizer()

        # Generate unique filename if needed
        filename = file.filename
        if not filename:
            import uuid
            ext = "jpg" if file.content_type == "image/jpeg" else "png"
            filename = f"reference_{uuid.uuid4().hex[:8]}.{ext}"

        success = recognizer.add_reference_photo(filename, contents)

        if success:
            return {"success": True, "filename": filename, "message": "Photo uploaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save photo")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/reference-photos/{filename}")
def delete_reference_photo(filename: str):
    """Delete a reference photo."""
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Face recognition not available")

    try:
        recognizer = get_recognizer()
        success = recognizer.remove_reference_photo(filename)

        if success:
            return {"success": True, "message": f"Photo '{filename}' deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"Photo '{filename}' not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/face-test")
def test_face_recognition(request: FaceTestRequest):
    """Test face recognition on a video URL."""
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Face recognition not available")

    try:
        recognizer = get_recognizer()
        result = recognizer.test_recognition(request.video_url)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/face-recognition/status")
def get_face_recognition_status():
    """Get face recognition system status."""
    if not FACE_RECOGNITION_AVAILABLE:
        return {
            "available": False,
            "model_loaded": False,
            "reference_photos": 0,
            "error": "Face recognition module not installed"
        }

    try:
        recognizer = get_recognizer()

        # Check if using DeepFace or OpenCV fallback
        try:
            from face_recognition import DEEPFACE_AVAILABLE
            using_fallback = not DEEPFACE_AVAILABLE
        except ImportError:
            using_fallback = True

        model_name = recognizer.config.get("model_name")
        if using_fallback:
            model_name = "OpenCV Haar Cascade (Detection Only)"

        return {
            "available": True,
            "model_loaded": recognizer.model_loaded,
            "reference_photos": len(recognizer.reference_image_paths),
            "fallback_mode": using_fallback,
            "config": {
                "model_name": model_name,
                "detector_backend": "opencv" if using_fallback else recognizer.config.get("detector_backend"),
                "frame_extraction_enabled": recognizer.config.get("enable_frame_extraction"),
            },
            "warning": "Using fallback mode: Can detect faces but cannot verify identity. Install TensorFlow with Python 3.11/3.12 for full recognition." if using_fallback else None
        }

    except Exception as e:
        return {
            "available": False,
            "model_loaded": False,
            "reference_photos": 0,
            "error": str(e)
        }


class VerifyFacesRequest(BaseModel):
    limit: Optional[int] = 10
    channel_filter: Optional[str] = None
    only_unverified: bool = True


@app.get("/api/face-verification/stats")
def get_face_verification_stats():
    """Get statistics about face verification status in the database."""
    try:
        stats = db.get_face_verification_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/face-verification/run")
def run_face_verification(request: VerifyFacesRequest):
    """
    Run face verification on videos in the database.

    This endpoint verifies faces in videos and updates their status.
    Limited to prevent timeout - use the CLI command for bulk verification.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Face recognition not available")

    try:
        # Import classifier
        from classifier import ContentClassifier, PHOTOS_DIR
        from models import ContentType

        # Get videos to verify
        videos = db.get_videos_for_face_verification(
            only_unverified=request.only_unverified,
            channel_filter=request.channel_filter,
            limit=min(request.limit or 10, 50)  # Max 50 to prevent timeout
        )

        if not videos:
            return {
                "success": True,
                "message": "No videos to verify",
                "processed": 0,
                "verified": 0,
                "not_verified": 0
            }

        # Initialize classifier
        classifier = ContentClassifier(use_frame_extraction=False)  # Thumbnails only for speed

        if classifier.face_recognizer is None:
            raise HTTPException(
                status_code=503,
                detail="Face recognizer not initialized. Check reference photos."
            )

        verified_count = 0
        not_verified_count = 0
        results = []

        for video in videos:
            try:
                face_verified, confidence = classifier._verify_face(video)

                if face_verified:
                    verified_count += 1
                    db.update_face_verification(
                        video_id=video.video_id,
                        face_verified=True,
                        confidence_score=confidence,
                        content_type=ContentType.PREACHING,
                        needs_review=False
                    )
                else:
                    not_verified_count += 1
                    is_strict = classifier._is_strict_channel(video.channel_name)
                    db.update_face_verification(
                        video_id=video.video_id,
                        face_verified=False,
                        confidence_score=confidence,
                        content_type=ContentType.UNKNOWN if is_strict else video.content_type,
                        needs_review=is_strict
                    )

                results.append({
                    "video_id": video.video_id,
                    "title": video.title[:50],
                    "verified": face_verified,
                    "confidence": confidence
                })

            except Exception as e:
                results.append({
                    "video_id": video.video_id,
                    "title": video.title[:50],
                    "error": str(e)
                })

        return {
            "success": True,
            "message": f"Verified {len(videos)} videos",
            "processed": len(videos),
            "verified": verified_count,
            "not_verified": not_verified_count,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAP ENDPOINTS
# =============================================================================

# Location coordinates for map visualization
LOCATION_COORDS = {
    "Pretoria": {"lat": -25.7479, "lng": 28.2293, "country": "South Africa", "isHomeBase": True},
    "Kinshasa": {"lat": -4.4419, "lng": 15.2663, "country": "DRC", "isHomeBase": False},
    "Lubumbashi": {"lat": -11.6647, "lng": 27.4794, "country": "DRC", "isHomeBase": False},
    "Likasi": {"lat": -10.9807, "lng": 26.7333, "country": "DRC", "isHomeBase": False},
    "Johannesburg": {"lat": -26.2041, "lng": 28.0473, "country": "South Africa", "isHomeBase": False},
    "Cape Town": {"lat": -33.9249, "lng": 18.4241, "country": "South Africa", "isHomeBase": False},
    "Durban": {"lat": -29.8587, "lng": 31.0218, "country": "South Africa", "isHomeBase": False},
    "Paris": {"lat": 48.8566, "lng": 2.3522, "country": "France", "isHomeBase": False},
    "London": {"lat": 51.5074, "lng": -0.1278, "country": "UK", "isHomeBase": False},
    "Brussels": {"lat": 50.8503, "lng": 4.3517, "country": "Belgium", "isHomeBase": False},
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points on Earth in km."""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def estimate_travel_time(distance_km: float) -> float:
    """Estimate travel time in hours based on distance."""
    # Assume flight for distances > 500km, otherwise driving
    if distance_km > 500:
        return distance_km / 500  # ~500 km/h avg including airport time
    else:
        return distance_km / 60  # ~60 km/h driving in Africa


@app.get("/api/map/locations")
def get_map_locations():
    """Get all locations with coordinates and sermon counts for map visualization."""
    df = db.get_all_sermons()

    if df.empty:
        return {"locations": []}

    # Known places mapping
    known_places = {
        "Pretoria": ["pretoria", "pta"],
        "Kinshasa": ["kinshasa", "rdc", "drc"],
        "Lubumbashi": ["lubumbashi"],
        "Likasi": ["likasi"],
        "Paris": ["paris", "france"],
        "London": ["london", "uk", "england"],
        "Brussels": ["brussels", "bruxelles", "belgium", "belgique"],
        "Johannesburg": ["johannesburg", "joburg", "jhb"],
        "Cape Town": ["cape town", "capetown"],
        "Durban": ["durban"],
    }

    def extract_place(row):
        text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
        for place, keywords in known_places.items():
            for keyword in keywords:
                if keyword in text:
                    return place
        return "Pretoria"  # Default home base

    df["place"] = df.apply(extract_place, axis=1)

    # Count sermons per location
    place_counts = df.groupby("place").size().to_dict()

    # Build location list with coordinates
    locations = []
    for place, coords in LOCATION_COORDS.items():
        sermon_count = place_counts.get(place, 0)
        locations.append({
            "name": place,
            "country": coords["country"],
            "lat": coords["lat"],
            "lng": coords["lng"],
            "sermonCount": sermon_count,
            "isHomeBase": coords["isHomeBase"]
        })

    # Sort by sermon count descending
    locations.sort(key=lambda x: x["sermonCount"], reverse=True)

    return {"locations": locations}


@app.get("/api/map/journeys")
def get_map_journeys(year: int = None):
    """Get travel journeys chronologically for route visualization."""
    from datetime import datetime

    df = db.get_all_sermons()

    if df.empty:
        return {"journeys": [], "totalTrips": 0, "totalDistanceKm": 0, "countriesVisited": 0}

    # Parse dates
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])

    # Filter by year if provided
    if year:
        df = df[df["date"].dt.year == year]

    # Known places mapping
    known_places = {
        "Pretoria": ["pretoria", "pta"],
        "Kinshasa": ["kinshasa", "rdc", "drc"],
        "Lubumbashi": ["lubumbashi"],
        "Likasi": ["likasi"],
        "Paris": ["paris", "france"],
        "London": ["london", "uk", "england"],
        "Brussels": ["brussels", "bruxelles", "belgium", "belgique"],
        "Johannesburg": ["johannesburg", "joburg", "jhb"],
        "Cape Town": ["cape town", "capetown"],
        "Durban": ["durban"],
    }

    def extract_place(row):
        text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
        for place, keywords in known_places.items():
            for keyword in keywords:
                if keyword in text:
                    return place
        return "Pretoria"

    df["place"] = df.apply(extract_place, axis=1)
    df = df.sort_values("date")

    # Track location changes (journeys)
    journeys = []
    prev_place = None
    prev_date = None
    countries_visited = set()
    total_distance = 0

    for _, row in df.iterrows():
        current_place = row["place"]
        current_date = row["date"]

        if current_place in LOCATION_COORDS:
            countries_visited.add(LOCATION_COORDS[current_place]["country"])

        if prev_place and prev_place != current_place:
            # Location changed - this is a journey
            if prev_place in LOCATION_COORDS and current_place in LOCATION_COORDS:
                from_coords = LOCATION_COORDS[prev_place]
                to_coords = LOCATION_COORDS[current_place]

                distance = haversine_distance(
                    from_coords["lat"], from_coords["lng"],
                    to_coords["lat"], to_coords["lng"]
                )
                travel_time = estimate_travel_time(distance)
                total_distance += distance

                journeys.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "from": prev_place,
                    "to": current_place,
                    "fromCoords": [from_coords["lat"], from_coords["lng"]],
                    "toCoords": [to_coords["lat"], to_coords["lng"]],
                    "distanceKm": round(distance),
                    "estimatedHours": round(travel_time, 1)
                })

        prev_place = current_place
        prev_date = current_date

    return {
        "journeys": journeys,
        "totalTrips": len(journeys),
        "totalDistanceKm": round(total_distance),
        "countriesVisited": len(countries_visited)
    }


@app.get("/api/map/travel-stats")
def get_travel_stats():
    """Get travel statistics by year and month."""
    from datetime import datetime

    df = db.get_all_sermons()

    if df.empty:
        return {
            "byYear": [],
            "byMonth": [],
            "totalTrips": 0,
            "totalDistanceKm": 0,
            "countriesVisited": 0,
            "citiesVisited": 0
        }

    # Parse dates
    df["date"] = df["upload_date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d") if x and len(str(x)) == 8 else None
    )
    df = df.dropna(subset=["date"])

    # Known places mapping
    known_places = {
        "Pretoria": ["pretoria", "pta"],
        "Kinshasa": ["kinshasa", "rdc", "drc"],
        "Lubumbashi": ["lubumbashi"],
        "Likasi": ["likasi"],
        "Paris": ["paris", "france"],
        "London": ["london", "uk", "england"],
        "Brussels": ["brussels", "bruxelles", "belgium", "belgique"],
        "Johannesburg": ["johannesburg", "joburg", "jhb"],
        "Cape Town": ["cape town", "capetown"],
        "Durban": ["durban"],
    }

    def extract_place(row):
        text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
        for place, keywords in known_places.items():
            for keyword in keywords:
                if keyword in text:
                    return place
        return "Pretoria"

    df["place"] = df.apply(extract_place, axis=1)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df = df.sort_values("date")

    # Calculate trips by year
    by_year = []
    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year].copy()
        year_df = year_df.sort_values("date")

        trips = 0
        distance = 0
        prev_place = None

        for _, row in year_df.iterrows():
            if prev_place and prev_place != row["place"]:
                trips += 1
                if prev_place in LOCATION_COORDS and row["place"] in LOCATION_COORDS:
                    distance += haversine_distance(
                        LOCATION_COORDS[prev_place]["lat"],
                        LOCATION_COORDS[prev_place]["lng"],
                        LOCATION_COORDS[row["place"]]["lat"],
                        LOCATION_COORDS[row["place"]]["lng"]
                    )
            prev_place = row["place"]

        by_year.append({
            "year": str(year),
            "trips": trips,
            "distanceKm": round(distance)
        })

    # Calculate trips by month (aggregate across all years)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    by_month = []

    for m in range(1, 13):
        month_df = df[df["month"] == m].copy()
        trips = 0
        prev_place = None

        for _, row in month_df.sort_values("date").iterrows():
            if prev_place and prev_place != row["place"]:
                trips += 1
            prev_place = row["place"]

        by_month.append({
            "month": month_names[m - 1],
            "trips": trips
        })

    # Total statistics
    total_trips = sum(y["trips"] for y in by_year)
    total_distance = sum(y["distanceKm"] for y in by_year)
    cities_visited = len(df["place"].unique())
    countries_visited = len(set(
        LOCATION_COORDS.get(p, {}).get("country", "Unknown")
        for p in df["place"].unique()
        if p in LOCATION_COORDS
    ))

    return {
        "byYear": by_year,
        "byMonth": by_month,
        "totalTrips": total_trips,
        "totalDistanceKm": total_distance,
        "countriesVisited": countries_visited,
        "citiesVisited": cities_visited
    }


# =============================================================================
# FORECASTING ENDPOINTS
# =============================================================================

@app.get("/api/forecast/sermons")
def get_sermon_forecast():
    """Get sermon count predictions for 2026 using XGBoost."""
    global forecaster

    if forecaster is None:
        return {
            "error": "Forecasting module not available",
            "historical": [],
            "predictions": [],
            "totalPredicted": 0,
            "confidence": 0,
            "modelMetrics": {}
        }

    try:
        df = db.get_all_sermons()

        if df.empty:
            return {
                "error": "No data available for training",
                "historical": [],
                "predictions": [],
                "totalPredicted": 0
            }

        # Prepare monthly data
        monthly_data = forecaster.prepare_monthly_data(df)

        if len(monthly_data) < 12:
            return {
                "error": "Not enough historical data (need at least 12 months)",
                "historical": [],
                "predictions": []
            }

        # Train model and get predictions
        metrics = forecaster.train_sermon_model(monthly_data)
        predictions = forecaster.predict_sermons_2026(monthly_data)
        historical = forecaster.get_historical_data(monthly_data)

        total_predicted = sum(p["value"] for p in predictions)

        # Calculate confidence based on model performance
        mae = metrics.get("mae", 2)
        avg_value = monthly_data["sermon_count"].mean()
        confidence = max(0, min(1, 1 - (mae / avg_value))) if avg_value > 0 else 0.5

        return {
            "historical": historical,
            "predictions": predictions,
            "totalPredicted": total_predicted,
            "confidence": round(confidence, 2),
            "modelMetrics": metrics
        }

    except Exception as e:
        return {
            "error": str(e),
            "historical": [],
            "predictions": [],
            "totalPredicted": 0
        }


@app.get("/api/forecast/trips")
def get_trip_forecast():
    """Get trip predictions for 2026 using XGBoost."""
    global forecaster

    if forecaster is None:
        return {
            "error": "Forecasting module not available",
            "historical": [],
            "predictions": [],
            "totalPredicted": 0
        }

    try:
        df = db.get_all_sermons()

        if df.empty:
            return {"error": "No data available", "historical": [], "predictions": []}

        # Prepare trip data
        trip_data = forecaster.prepare_trip_data(df)

        if len(trip_data) < 12:
            return {"error": "Not enough trip data", "historical": [], "predictions": []}

        # Train model and get predictions
        metrics = forecaster.train_trip_model(trip_data)
        predictions = forecaster.predict_trips_2026(trip_data)

        # Get historical trip data
        historical = [
            {
                "period": str(row["year_month"]),
                "trips": int(row["trips"])
            }
            for _, row in trip_data.iterrows()
        ]

        total_predicted = sum(p["trips"] for p in predictions)

        # Estimate total distance for predicted trips
        avg_trip_distance = 2000  # Average km per trip based on common routes
        predicted_distance = total_predicted * avg_trip_distance

        return {
            "historical": historical,
            "predictions": predictions,
            "totalPredicted": total_predicted,
            "predictedDistanceKm": predicted_distance,
            "modelMetrics": metrics
        }

    except Exception as e:
        return {"error": str(e), "historical": [], "predictions": []}


@app.get("/api/forecast/model-status")
def get_forecast_model_status():
    """Get current model training status."""
    global forecaster

    if forecaster is None:
        return {
            "sermonModel": {"trained": False},
            "tripModel": {"trained": False},
            "xgboostAvailable": False
        }

    return forecaster.get_model_status()


@app.post("/api/forecast/retrain")
def retrain_forecast_models():
    """Retrain forecast models with latest data."""
    global forecaster

    if forecaster is None:
        return {"success": False, "error": "Forecasting module not available"}

    try:
        df = db.get_all_sermons()

        # Train sermon model
        monthly_data = forecaster.prepare_monthly_data(df)
        sermon_metrics = forecaster.train_sermon_model(monthly_data)

        # Train trip model
        trip_data = forecaster.prepare_trip_data(df)
        trip_metrics = forecaster.train_trip_model(trip_data)

        return {
            "success": True,
            "message": "Models retrained successfully",
            "sermonMetrics": sermon_metrics,
            "tripMetrics": trip_metrics
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# HEALTH INSIGHTS ENDPOINTS
# =============================================================================

@app.get("/api/health/score")
def get_health_score():
    """Get current health score (0-100) with breakdown."""
    if not HEALTH_AVAILABLE:
        return {
            "error": "Health insights module not available",
            "score": 50,
            "status": "unknown",
            "breakdown": {}
        }

    try:
        health_engine = HealthInsightsEngine(db)
        return health_engine.calculate_health_score()
    except Exception as e:
        return {"error": str(e), "score": 50, "status": "error"}


@app.get("/api/health/metrics")
def get_health_metrics():
    """Get raw health metrics for dashboard display."""
    if not HEALTH_AVAILABLE:
        return {"error": "Health insights module not available"}

    try:
        health_engine = HealthInsightsEngine(db)
        return health_engine.get_health_metrics()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/health/report")
def get_health_report():
    """Generate comprehensive health report with AI insights."""
    if not HEALTH_AVAILABLE:
        return {
            "error": "Health insights module not available",
            "ollamaAvailable": False,
            "aiGenerated": False
        }

    try:
        health_engine = HealthInsightsEngine(db)
        return health_engine.generate_health_report()
    except Exception as e:
        return {"error": str(e), "ollamaAvailable": False}


@app.get("/api/health/trends")
def get_health_trends(weeks: int = 12):
    """Get workload trends for the last N weeks."""
    if not HEALTH_AVAILABLE:
        return {"error": "Health insights module not available", "trends": []}

    try:
        health_engine = HealthInsightsEngine(db)
        trends = health_engine.get_workload_trends(weeks)
        return {"trends": trends}
    except Exception as e:
        return {"error": str(e), "trends": []}


# =============================================================================
# PLANNING ENDPOINTS
# =============================================================================

@app.get("/api/planning/report")
def get_planning_report():
    """Generate AI-powered planning recommendations."""
    if not PLANNING_AVAILABLE:
        return {
            "error": "Planning module not available",
            "ollamaAvailable": False,
            "aiGenerated": False
        }

    try:
        planning_engine = PlanningEngine(db, forecaster)
        return planning_engine.generate_planning_report()
    except Exception as e:
        return {"error": str(e), "ollamaAvailable": False}


@app.get("/api/planning/upcoming")
def get_upcoming_predictions():
    """Get forecast-based upcoming ministry predictions."""
    if not PLANNING_AVAILABLE:
        return {"error": "Planning module not available"}

    try:
        planning_engine = PlanningEngine(db, forecaster)
        return planning_engine.get_upcoming_predictions()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/planning/patterns")
def get_historical_patterns():
    """Get historical ministry patterns for planning."""
    if not PLANNING_AVAILABLE:
        return {"error": "Planning module not available"}

    try:
        planning_engine = PlanningEngine(db, forecaster)
        return planning_engine.get_historical_patterns()
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# AI STATUS ENDPOINT
# =============================================================================

@app.get("/api/ai/status")
def get_ai_status():
    """Check Ollama availability and model status."""
    if ollama_service is None:
        return {
            "available": False,
            "model": None,
            "message": "Ollama service not imported"
        }

    try:
        return ollama_service.check_availability_sync()
    except Exception as e:
        return {
            "available": False,
            "model": None,
            "message": f"Error checking Ollama: {str(e)}"
        }


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    """Serve the minimal frontend."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ministry Analytics - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #333;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #4A148C 0%, #7B1FA2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }

        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        .header p {
            opacity: 0.9;
            font-size: 1rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }

        .stat-card .value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #4A148C;
            margin-bottom: 0.5rem;
        }

        .stat-card .label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card.gold .value {
            color: #B8860B;
        }

        .section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .section h2 {
            color: #4A148C;
            margin-bottom: 1rem;
            font-size: 1.25rem;
            border-bottom: 2px solid #FFD700;
            padding-bottom: 0.5rem;
            display: inline-block;
        }

        .channel-list {
            list-style: none;
        }

        .channel-list li {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid #eee;
        }

        .channel-list li:last-child {
            border-bottom: none;
        }

        .channel-name {
            font-weight: 500;
        }

        .channel-count {
            background: #4A148C;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
        }

        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
        }

        .video-card {
            background: #fafafa;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s;
        }

        .video-card:hover {
            transform: scale(1.02);
        }

        .video-card img {
            width: 100%;
            height: 160px;
            object-fit: cover;
            background: #ddd;
        }

        .video-card .info {
            padding: 1rem;
        }

        .video-card .title {
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .video-card .meta {
            font-size: 0.8rem;
            color: #666;
        }

        .video-card a {
            color: #4A148C;
            text-decoration: none;
        }

        .video-card a:hover {
            text-decoration: underline;
        }

        .badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-right: 0.5rem;
        }

        .badge.preaching {
            background: #e8f5e9;
            color: #2e7d32;
        }

        .badge.unknown {
            background: #fff3e0;
            color: #e65100;
        }

        .badge.fr {
            background: #e3f2fd;
            color: #1565c0;
        }

        .badge.en {
            background: #fce4ec;
            color: #c2185b;
        }

        .loading {
            text-align: center;
            padding: 3rem;
            color: #666;
        }

        .error {
            background: #ffebee;
            color: #c62828;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }

        .refresh-btn {
            background: #4A148C;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 1rem;
            transition: background 0.2s;
        }

        .refresh-btn:hover {
            background: #7B1FA2;
        }

        .date-range {
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Ministry Analytics Platform</h1>
        <p>Apostle Narcisse Majila - Sermon Tracker</p>
    </div>

    <div class="container">
        <div id="stats-section">
            <div class="loading">Loading statistics...</div>
        </div>

        <div id="channels-section" class="section" style="display:none;">
            <h2>Top Channels</h2>
            <ul class="channel-list" id="channel-list"></ul>
        </div>

        <div id="videos-section" class="section" style="display:none;">
            <h2>Recent Sermons</h2>
            <div class="video-grid" id="video-grid"></div>
        </div>

        <div style="text-align: center;">
            <button class="refresh-btn" onclick="loadData()">Refresh Data</button>
        </div>
    </div>

    <script>
        async function loadData() {
            // Load stats
            try {
                const statsRes = await fetch('/api/stats');
                const stats = await statsRes.json();
                renderStats(stats);
            } catch (err) {
                document.getElementById('stats-section').innerHTML =
                    '<div class="error">Failed to load statistics. Make sure the database exists.</div>';
            }

            // Load videos
            try {
                const videosRes = await fetch('/api/videos?limit=6');
                const data = await videosRes.json();
                renderVideos(data.videos);
            } catch (err) {
                console.error('Failed to load videos:', err);
            }
        }

        function renderStats(stats) {
            const preaching = stats.by_content_type?.PREACHING || 0;
            const unknown = stats.by_content_type?.UNKNOWN || 0;
            const sermons = preaching + unknown;

            const hours = stats.total_preaching_hours || 0;
            const h = Math.floor(hours);
            const m = Math.round((hours - h) * 60);

            let dateRange = '';
            if (stats.oldest_video && stats.newest_video) {
                const oldest = formatDate(stats.oldest_video);
                const newest = formatDate(stats.newest_video);
                dateRange = `<div class="date-range">From ${oldest} to ${newest}</div>`;
            }

            document.getElementById('stats-section').innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="value">${stats.total_videos}</div>
                        <div class="label">Total Videos</div>
                    </div>
                    <div class="stat-card gold">
                        <div class="value">${sermons}</div>
                        <div class="label">Preaching Videos</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${h}h ${m}m</div>
                        <div class="label">Total Duration</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${stats.unique_channels}</div>
                        <div class="label">Channels</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${stats.needs_review}</div>
                        <div class="label">Need Review</div>
                    </div>
                </div>
                ${dateRange}
            `;

            // Render channels
            if (stats.top_channels && stats.top_channels.length > 0) {
                document.getElementById('channels-section').style.display = 'block';
                const list = document.getElementById('channel-list');
                list.innerHTML = stats.top_channels.map(ch => `
                    <li>
                        <span class="channel-name">${ch.name}</span>
                        <span class="channel-count">${ch.count} videos</span>
                    </li>
                `).join('');
            }
        }

        function renderVideos(videos) {
            if (!videos || videos.length === 0) return;

            document.getElementById('videos-section').style.display = 'block';
            const grid = document.getElementById('video-grid');

            grid.innerHTML = videos.map(v => {
                const thumb = v.thumbnail_url || 'https://via.placeholder.com/320x180?text=No+Thumbnail';
                const duration = formatDuration(v.duration);
                const date = formatDate(v.upload_date);
                const views = v.view_count ? v.view_count.toLocaleString() + ' views' : '';
                const contentBadge = v.content_type === 'PREACHING'
                    ? '<span class="badge preaching">PREACHING</span>'
                    : '<span class="badge unknown">UNKNOWN</span>';
                const langBadge = v.language === 'FR'
                    ? '<span class="badge fr">FR</span>'
                    : v.language === 'EN' ? '<span class="badge en">EN</span>' : '';

                return `
                    <div class="video-card">
                        <a href="${v.video_url}" target="_blank">
                            <img src="${thumb}" alt="${v.title}" onerror="this.src='https://via.placeholder.com/320x180?text=No+Thumbnail'">
                        </a>
                        <div class="info">
                            <div class="title">
                                <a href="${v.video_url}" target="_blank">${v.title || 'Untitled'}</a>
                            </div>
                            <div class="meta">${v.channel_name || 'Unknown Channel'}</div>
                            <div class="meta">${duration} • ${date} ${views ? '• ' + views : ''}</div>
                            <div style="margin-top: 0.5rem;">
                                ${contentBadge}${langBadge}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function formatDuration(seconds) {
            if (!seconds) return 'Unknown';
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
            return `${m}:${s.toString().padStart(2, '0')}`;
        }

        function formatDate(dateStr) {
            if (!dateStr || dateStr.length !== 8) return 'Unknown';
            return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6)}`;
        }

        // Load data on page load
        loadData();
    </script>
</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
