"""
Health Insights Engine - AI-Powered Health Analysis for Ministry
Calculates health scores and generates AI reports using Ollama.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from ollama_service import ollama_service


class HealthInsightsEngine:
    """Engine for calculating health metrics and generating AI health reports."""

    # Health score weights
    WEIGHTS = {
        "weekly_workload": 0.25,
        "monthly_travel": 0.20,
        "hours_preached": 0.20,
        "rest_deficit": 0.20,
        "upcoming_load": 0.15
    }

    # System prompt for AI Doctor
    DOCTOR_SYSTEM_PROMPT = """You are an AI Health Advisor for Apostle Narcisse Majila, a Christian pastor who travels internationally for ministry across Africa and Europe.

Your role is to analyze his workload data and provide health recommendations that honor both his calling and his wellbeing.

Guidelines:
- Be respectful and supportive of his ministry calling
- Focus on sustainable ministry practices for long-term effectiveness
- Recommend specific rest periods and sleep requirements
- Consider travel fatigue, jet lag, and the physical demands of preaching
- Suggest optimal preaching limits per week/month
- Use a caring but professional tone
- Be specific with numbers (e.g., "7-8 hours of sleep" not just "adequate sleep")

You MUST respond with ONLY valid JSON in this exact format:
{
    "summary": "A 2-3 sentence overview of current health status",
    "concerns": ["List of 2-4 specific health concerns based on the data"],
    "restRecommendations": ["List of 2-4 specific rest recommendations"],
    "sleepGuidelines": ["List of 2-3 sleep-related guidelines"],
    "holidayRecommendations": ["List of 2-3 holiday/vacation recommendations"],
    "positiveObservations": ["List of 1-3 positive observations about their schedule"]
}"""

    def __init__(self, database):
        """Initialize with database reference."""
        self.db = database

    def get_health_metrics(self) -> Dict[str, Any]:
        """
        Calculate current health metrics from sermon data.
        Returns raw metrics used for score calculation.
        """
        df = self.db.get_all_sermons()

        if df.empty:
            return self._empty_metrics()

        # Parse dates
        df['date'] = pd.to_datetime(df['upload_date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['date'])

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # This week metrics
        week_sermons = df[df['date'] >= week_ago]
        sermons_this_week = len(week_sermons)
        hours_this_week = round(week_sermons['duration'].sum() / 3600, 1) if 'duration' in week_sermons.columns else 0

        # This month metrics
        month_sermons = df[df['date'] >= month_ago]
        sermons_this_month = len(month_sermons)
        hours_this_month = round(month_sermons['duration'].sum() / 3600, 1) if 'duration' in month_sermons.columns else 0

        # Calculate trips this month (location changes)
        trips_this_month = self._calculate_trips(month_sermons)

        # Calculate travel distance this month
        travel_km = self._estimate_travel_distance(month_sermons)

        # Days since last extended rest (7+ consecutive days without sermon)
        days_since_rest = self._calculate_days_since_rest(df)

        # Consecutive busy weeks (weeks with 2+ sermons)
        consecutive_busy_weeks = self._calculate_consecutive_busy_weeks(df)

        return {
            "sermonsThisWeek": sermons_this_week,
            "hoursThisWeek": hours_this_week,
            "sermonsThisMonth": sermons_this_month,
            "hoursThisMonth": hours_this_month,
            "tripsThisMonth": trips_this_month,
            "daysSinceRest": days_since_rest,
            "consecutiveBusyWeeks": consecutive_busy_weeks,
            "travelThisMonthKm": travel_km,
            "calculatedAt": now.isoformat()
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics when no data available."""
        return {
            "sermonsThisWeek": 0,
            "hoursThisWeek": 0,
            "sermonsThisMonth": 0,
            "hoursThisMonth": 0,
            "tripsThisMonth": 0,
            "daysSinceRest": 0,
            "consecutiveBusyWeeks": 0,
            "travelThisMonthKm": 0,
            "calculatedAt": datetime.now().isoformat()
        }

    def _calculate_trips(self, df: pd.DataFrame) -> int:
        """Calculate number of location changes (trips) in the data."""
        if df.empty:
            return 0

        # Extract locations from channel names/titles
        locations = {
            'Kinshasa': ['kinshasa', 'rdc', 'drc'],
            'Lubumbashi': ['lubumbashi'],
            'Likasi': ['likasi'],
            'Paris': ['paris', 'france'],
            'London': ['london', 'uk'],
            'Brussels': ['brussels', 'bruxelles', 'belgium'],
            'Johannesburg': ['johannesburg', 'joburg', 'jhb'],
            'Cape Town': ['cape town', 'capetown'],
            'Durban': ['durban'],
            'Pretoria': ['pretoria', 'pta']
        }

        def extract_location(row):
            text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
            for loc, keywords in locations.items():
                for kw in keywords:
                    if kw in text:
                        return loc
            return 'Pretoria'  # Default home base

        df = df.copy()
        df['location'] = df.apply(extract_location, axis=1)
        df = df.sort_values('date')

        # Count location changes
        trips = 0
        prev_loc = None
        for _, row in df.iterrows():
            if prev_loc and prev_loc != row['location']:
                trips += 1
            prev_loc = row['location']

        return trips

    def _estimate_travel_distance(self, df: pd.DataFrame) -> int:
        """Estimate total travel distance in km."""
        # Distance matrix (approximate km between locations)
        distances = {
            ('Pretoria', 'Kinshasa'): 2850,
            ('Pretoria', 'Lubumbashi'): 1950,
            ('Pretoria', 'Likasi'): 1900,
            ('Pretoria', 'Johannesburg'): 60,
            ('Pretoria', 'Cape Town'): 1400,
            ('Pretoria', 'Durban'): 650,
            ('Pretoria', 'Paris'): 8900,
            ('Pretoria', 'London'): 9000,
            ('Pretoria', 'Brussels'): 8800,
            ('Kinshasa', 'Lubumbashi'): 1500,
            ('Kinshasa', 'Likasi'): 1400,
        }

        if df.empty:
            return 0

        # Get trips with locations
        locations_map = {
            'Kinshasa': ['kinshasa', 'rdc', 'drc'],
            'Lubumbashi': ['lubumbashi'],
            'Likasi': ['likasi'],
            'Paris': ['paris', 'france'],
            'London': ['london', 'uk'],
            'Brussels': ['brussels', 'bruxelles', 'belgium'],
            'Johannesburg': ['johannesburg', 'joburg', 'jhb'],
            'Cape Town': ['cape town', 'capetown'],
            'Durban': ['durban'],
            'Pretoria': ['pretoria', 'pta']
        }

        def extract_location(row):
            text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
            for loc, keywords in locations_map.items():
                for kw in keywords:
                    if kw in text:
                        return loc
            return 'Pretoria'

        df = df.copy()
        df['location'] = df.apply(extract_location, axis=1)
        df = df.sort_values('date')

        total_km = 0
        prev_loc = None
        for _, row in df.iterrows():
            curr_loc = row['location']
            if prev_loc and prev_loc != curr_loc:
                # Look up distance
                key1 = (prev_loc, curr_loc)
                key2 = (curr_loc, prev_loc)
                dist = distances.get(key1) or distances.get(key2) or 500  # Default 500km
                total_km += dist
            prev_loc = curr_loc

        return int(total_km)

    def _calculate_days_since_rest(self, df: pd.DataFrame) -> int:
        """Calculate days since last extended rest period (7+ days without sermon)."""
        if df.empty:
            return 0

        df = df.sort_values('date', ascending=False)
        dates = df['date'].dt.date.unique()

        if len(dates) == 0:
            return 0

        # Find longest gap in recent history
        today = datetime.now().date()
        last_sermon = dates[0]
        days_since_last = (today - last_sermon).days

        # If more than 7 days since last sermon, that counts as rest
        if days_since_last >= 7:
            return 0

        # Otherwise, look for gaps between sermons
        sorted_dates = sorted(dates, reverse=True)
        for i in range(len(sorted_dates) - 1):
            gap = (sorted_dates[i] - sorted_dates[i + 1]).days
            if gap >= 7:
                # Found a rest period, count days since it ended
                return (today - sorted_dates[i]).days

        # No rest period found in data, return days since oldest sermon
        return min((today - sorted_dates[-1]).days, 90)  # Cap at 90 days

    def _calculate_consecutive_busy_weeks(self, df: pd.DataFrame) -> int:
        """Calculate consecutive weeks with 2+ sermons."""
        if df.empty:
            return 0

        df = df.copy()
        df['week'] = df['date'].dt.isocalendar().week
        df['year'] = df['date'].dt.year

        # Get recent weeks
        now = datetime.now()
        recent = df[df['date'] >= (now - timedelta(days=56))]  # Last 8 weeks

        if recent.empty:
            return 0

        # Count sermons per week
        weekly = recent.groupby(['year', 'week']).size()

        # Count consecutive busy weeks (2+ sermons)
        consecutive = 0
        max_consecutive = 0

        for count in weekly.values:
            if count >= 2:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0

        return max_consecutive

    def calculate_health_score(self, metrics: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Calculate health score (0-100) from metrics.
        Lower score = better health, Higher score = more concern
        """
        if metrics is None:
            metrics = self.get_health_metrics()

        # Calculate individual component scores (0-100, higher = worse)
        weekly_workload = min(100, max(0, metrics['sermonsThisWeek'] * 15))
        monthly_travel = min(100, max(0, metrics['travelThisMonthKm'] / 100))
        hours_preached = min(100, max(0, metrics['hoursThisMonth'] * 5))
        rest_deficit = min(100, max(0, metrics['daysSinceRest'] * 5))
        upcoming_load = min(100, max(0, metrics['consecutiveBusyWeeks'] * 20))

        # Weighted average
        score = (
            self.WEIGHTS['weekly_workload'] * weekly_workload +
            self.WEIGHTS['monthly_travel'] * monthly_travel +
            self.WEIGHTS['hours_preached'] * hours_preached +
            self.WEIGHTS['rest_deficit'] * rest_deficit +
            self.WEIGHTS['upcoming_load'] * upcoming_load
        )

        score = round(score)

        # Determine status
        if score <= 40:
            status = "good"
        elif score <= 70:
            status = "moderate"
        else:
            status = "high"

        return {
            "score": score,
            "status": status,
            "breakdown": {
                "weeklyWorkload": round(weekly_workload),
                "monthlyTravel": round(monthly_travel),
                "hoursPreached": round(hours_preached),
                "restDeficit": round(rest_deficit),
                "upcomingLoad": round(upcoming_load)
            }
        }

    def get_workload_trends(self, weeks: int = 12) -> List[Dict]:
        """Get weekly workload data for trend visualization."""
        df = self.db.get_all_sermons()

        if df.empty:
            return []

        df['date'] = pd.to_datetime(df['upload_date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['date'])

        # Get data for last N weeks
        cutoff = datetime.now() - timedelta(weeks=weeks)
        df = df[df['date'] >= cutoff]

        if df.empty:
            return []

        df['week'] = df['date'].dt.isocalendar().week
        df['year'] = df['date'].dt.year
        df['week_start'] = df['date'] - pd.to_timedelta(df['date'].dt.dayofweek, unit='D')

        # Aggregate by week
        weekly = df.groupby('week_start').agg({
            'video_id': 'count',
            'duration': 'sum'
        }).reset_index()

        weekly.columns = ['week_start', 'sermons', 'duration']
        weekly['hours'] = round(weekly['duration'] / 3600, 1)
        weekly['week_start'] = weekly['week_start'].dt.strftime('%Y-%m-%d')

        return weekly[['week_start', 'sermons', 'hours']].to_dict('records')

    def _build_rag_context(self, metrics: Dict, score: Dict) -> str:
        """Build context string for RAG prompt."""
        context = f"""
CURRENT HEALTH METRICS FOR APOSTLE NARCISSE MAJILA:

Date: {datetime.now().strftime('%Y-%m-%d')}

WORKLOAD SUMMARY:
- Sermons this week: {metrics['sermonsThisWeek']}
- Hours preached this week: {metrics['hoursThisWeek']}
- Sermons this month: {metrics['sermonsThisMonth']}
- Hours preached this month: {metrics['hoursThisMonth']}
- Trips this month: {metrics['tripsThisMonth']}
- Travel distance this month: {metrics['travelThisMonthKm']} km

REST INDICATORS:
- Days since last extended rest (7+ days off): {metrics['daysSinceRest']}
- Consecutive busy weeks (2+ sermons/week): {metrics['consecutiveBusyWeeks']}

HEALTH SCORE: {score['score']}/100 ({score['status'].upper()})
- Weekly Workload Risk: {score['breakdown']['weeklyWorkload']}/100
- Monthly Travel Risk: {score['breakdown']['monthlyTravel']}/100
- Hours Preached Risk: {score['breakdown']['hoursPreached']}/100
- Rest Deficit Risk: {score['breakdown']['restDeficit']}/100
- Upcoming Load Risk: {score['breakdown']['upcomingLoad']}/100

INTERPRETATION:
- Score 0-40: Good (sustainable workload)
- Score 41-70: Moderate (monitor closely)
- Score 71-100: High Risk (rest needed urgently)

Based on this data, provide personalized health recommendations.
"""
        return context

    def generate_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive health report using AI.
        Falls back to rule-based report if Ollama unavailable.
        """
        metrics = self.get_health_metrics()
        score = self.calculate_health_score(metrics)

        # Check Ollama availability
        ollama_status = ollama_service.check_availability_sync()

        if ollama_status.get('available'):
            # Generate AI report
            context = self._build_rag_context(metrics, score)
            prompt = f"{context}\n\nGenerate a health report based on this data."

            result = ollama_service.generate_json(
                prompt=prompt,
                system_prompt=self.DOCTOR_SYSTEM_PROMPT,
                temperature=0.4
            )

            if result.get('success') and result.get('data'):
                ai_report = result['data']
                return {
                    "generatedAt": datetime.now().isoformat(),
                    "score": score,
                    "metrics": metrics,
                    "summary": ai_report.get('summary', ''),
                    "concerns": ai_report.get('concerns', []),
                    "restRecommendations": ai_report.get('restRecommendations', []),
                    "sleepGuidelines": ai_report.get('sleepGuidelines', []),
                    "holidayRecommendations": ai_report.get('holidayRecommendations', []),
                    "positiveObservations": ai_report.get('positiveObservations', []),
                    "ollamaAvailable": True,
                    "aiGenerated": True
                }

        # Fallback to rule-based report
        return self._generate_fallback_report(metrics, score, ollama_status.get('available', False))

    def _generate_fallback_report(self, metrics: Dict, score: Dict, ollama_available: bool) -> Dict[str, Any]:
        """Generate rule-based report when AI is unavailable."""
        concerns = []
        rest_recommendations = []
        sleep_guidelines = []
        holiday_recommendations = []
        positive_observations = []

        # Analyze metrics and generate rules-based insights
        if metrics['consecutiveBusyWeeks'] >= 3:
            concerns.append(f"{metrics['consecutiveBusyWeeks']} consecutive weeks with heavy preaching schedule")

        if metrics['daysSinceRest'] > 14:
            concerns.append(f"{metrics['daysSinceRest']} days since last extended rest period")

        if metrics['travelThisMonthKm'] > 3000:
            concerns.append(f"High travel intensity this month ({metrics['travelThisMonthKm']} km)")

        if metrics['hoursThisMonth'] > 15:
            concerns.append(f"Significant preaching hours this month ({metrics['hoursThisMonth']} hours)")

        # Rest recommendations
        if metrics['sermonsThisWeek'] >= 2:
            rest_recommendations.append("Take at least 2 full rest days this week")
        else:
            rest_recommendations.append("Maintain current rest pattern - looks sustainable")

        if metrics['daysSinceRest'] > 21:
            rest_recommendations.append("Schedule an extended rest period (3-5 days) within the next 2 weeks")

        rest_recommendations.append("Avoid scheduling back-to-back sermon days when possible")

        # Sleep guidelines
        sleep_guidelines.append("Aim for 7-8 hours of sleep per night")
        if metrics['tripsThisMonth'] > 0:
            sleep_guidelines.append("After international travel, allow extra rest for jet lag recovery")
        sleep_guidelines.append("Maintain consistent sleep schedule even during busy ministry periods")

        # Holiday recommendations
        if metrics['consecutiveBusyWeeks'] >= 4:
            holiday_recommendations.append("Schedule a 7-day ministry break within the next 4-6 weeks")
        else:
            holiday_recommendations.append("Plan quarterly rest periods of 5-7 days")

        holiday_recommendations.append("Consider scheduling holidays during historically low-activity months")

        # Positive observations
        if metrics['sermonsThisWeek'] <= 2:
            positive_observations.append("Current weekly sermon count is within sustainable limits")

        if metrics['hoursThisWeek'] < 5:
            positive_observations.append("Weekly preaching hours are well-balanced")

        if len(positive_observations) == 0:
            positive_observations.append("Your dedication to ministry is evident - remember to care for yourself too")

        # Generate summary
        status_text = {
            "good": "Your current workload appears sustainable.",
            "moderate": "Your workload requires attention - some adjustments recommended.",
            "high": "Your current workload is concerning - rest is urgently needed."
        }

        summary = f"Health score: {score['score']}/100 ({score['status']}). {status_text[score['status']]} You've preached {metrics['sermonsThisMonth']} sermons totaling {metrics['hoursThisMonth']} hours this month."

        return {
            "generatedAt": datetime.now().isoformat(),
            "score": score,
            "metrics": metrics,
            "summary": summary,
            "concerns": concerns if concerns else ["No major concerns at this time"],
            "restRecommendations": rest_recommendations,
            "sleepGuidelines": sleep_guidelines,
            "holidayRecommendations": holiday_recommendations,
            "positiveObservations": positive_observations,
            "ollamaAvailable": ollama_available,
            "aiGenerated": False
        }
