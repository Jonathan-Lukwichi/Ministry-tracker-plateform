"""
Planning Engine - AI-Powered Ministry Planning Assistant
Generates trip planning, meeting schedules, and ministry recommendations using Ollama.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

from ollama_service import ollama_service


class PlanningEngine:
    """Engine for generating AI-powered ministry planning recommendations."""

    # System prompt for AI Planning Assistant
    PLANNER_SYSTEM_PROMPT = """You are an AI Ministry Planning Assistant for the team of Apostle Narcisse Majila, a pastor who leads Ramah Full Gospel Church in Pretoria, South Africa.

Your role is to help plan trips, meetings, and ministry activities based on historical patterns and forecasts.

Key locations in the ministry:
- Pretoria, South Africa (Home base - Ramah Full Gospel Church)
- Kinshasa, DRC
- Lubumbashi, DRC
- Likasi, DRC
- Paris, France
- London, UK
- Brussels, Belgium

Guidelines:
- Consider historical ministry patterns when making recommendations
- Factor in the pastor's health and workload when suggesting schedules
- Suggest optimal times for international trips based on low-activity periods
- Recommend meeting schedules that avoid burnout
- Balance ministry effectiveness with wellbeing
- Be specific with dates and timeframes
- Consider travel logistics (flights, time zones, recovery)

You MUST respond with ONLY valid JSON in this exact format:
{
    "upcomingOverview": "2-3 sentence overview of the upcoming month based on patterns",
    "tripRecommendations": [
        {"destination": "City name", "suggestedPeriod": "Date range", "reason": "Why this timing", "priority": "high/medium/low"}
    ],
    "meetingSuggestions": [
        {"type": "Meeting type", "suggestedDay": "Day of week", "suggestedTime": "Morning/Afternoon/Evening", "reason": "Why this timing"}
    ],
    "restWindows": [
        {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "type": "rest", "note": "Purpose of this rest period"}
    ],
    "highDemandWarnings": ["List of upcoming high-demand periods to prepare for"]
}"""

    def __init__(self, database, forecaster=None):
        """Initialize with database and optional forecaster reference."""
        self.db = database
        self.forecaster = forecaster

    def get_upcoming_predictions(self) -> Dict[str, Any]:
        """Get predictions for the upcoming month."""
        now = datetime.now()
        next_month = now.month % 12 + 1
        next_month_year = now.year if next_month > 1 else now.year + 1

        # Get forecast predictions if available
        predicted_sermons = 0
        predicted_trips = 0

        if self.forecaster:
            try:
                df = self.db.get_all_sermons()
                if not df.empty:
                    monthly_data = self.forecaster.prepare_monthly_data(df)
                    if len(monthly_data) >= 12:
                        self.forecaster.train_sermon_model(monthly_data)
                        sermon_predictions = self.forecaster.predict_sermons_2026(monthly_data)

                        # Find prediction for next month
                        for pred in sermon_predictions:
                            if pred['period'] == f"2026-{next_month:02d}":
                                predicted_sermons = pred['value']
                                break

                        # Trip predictions
                        trip_data = self.forecaster.prepare_trip_data(df)
                        if len(trip_data) >= 12:
                            self.forecaster.train_trip_model(trip_data)
                            trip_predictions = self.forecaster.predict_trips_2026(trip_data)

                            for pred in trip_predictions:
                                if pred['period'] == f"2026-{next_month:02d}":
                                    predicted_trips = pred['trips']
                                    break
            except Exception as e:
                print(f"Forecasting error: {e}")

        # Get health score
        health_score = 50  # Default
        try:
            from health_insights import HealthInsightsEngine
            health_engine = HealthInsightsEngine(self.db)
            score_data = health_engine.calculate_health_score()
            health_score = score_data.get('score', 50)
        except Exception:
            pass

        # Find historically busy days
        busy_days = self._get_historically_busy_days(next_month)

        return {
            "nextMonth": {
                "month": next_month,
                "year": next_month_year,
                "monthName": datetime(2000, next_month, 1).strftime('%B'),
                "predictedSermons": predicted_sermons,
                "predictedTrips": predicted_trips,
                "healthScore": health_score,
                "busyDays": busy_days
            }
        }

    def _get_historically_busy_days(self, month: int) -> List[str]:
        """Get historically busy days for a given month."""
        df = self.db.get_all_sermons()

        if df.empty:
            return []

        df['date'] = pd.to_datetime(df['upload_date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['date'])

        # Filter to the target month across all years
        month_data = df[df['date'].dt.month == month]

        if month_data.empty:
            return []

        # Count sermons by day of month
        day_counts = month_data['date'].dt.day.value_counts()

        # Get top 3 busiest days
        busy_days = day_counts.nlargest(3).index.tolist()

        # Format as dates for upcoming month
        year = datetime.now().year
        if month <= datetime.now().month:
            year += 1

        return [f"{year}-{month:02d}-{day:02d}" for day in sorted(busy_days)]

    def get_historical_patterns(self) -> Dict[str, Any]:
        """Get historical ministry patterns for planning."""
        df = self.db.get_all_sermons()

        if df.empty:
            return self._empty_patterns()

        df['date'] = pd.to_datetime(df['upload_date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['date'])

        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday

        # Average sermons per month
        monthly_avg = df.groupby('month').size().reset_index(name='count')
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_patterns = []
        for m in range(1, 13):
            avg = monthly_avg[monthly_avg['month'] == m]['count'].values
            avg_count = float(avg[0]) if len(avg) > 0 else 0
            # Average across years
            years = df['date'].dt.year.nunique()
            if years > 0:
                avg_count = round(avg_count / years, 1)
            monthly_patterns.append({
                "month": month_names[m - 1],
                "avgSermons": avg_count
            })

        # Day of week patterns
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_counts = df['day_of_week'].value_counts().sort_index()
        daily_patterns = []
        for d in range(7):
            count = dow_counts.get(d, 0)
            daily_patterns.append({
                "day": day_names[d],
                "sermons": int(count)
            })

        # Busiest and quietest months
        busiest_month = monthly_avg.loc[monthly_avg['count'].idxmax(), 'month'] if not monthly_avg.empty else 1
        quietest_month = monthly_avg.loc[monthly_avg['count'].idxmin(), 'month'] if not monthly_avg.empty else 1

        # Location frequency
        locations = self._get_location_frequency(df)

        return {
            "monthlyPatterns": monthly_patterns,
            "dailyPatterns": daily_patterns,
            "busiestMonth": month_names[busiest_month - 1],
            "quietestMonth": month_names[quietest_month - 1],
            "locationFrequency": locations,
            "totalSermons": len(df),
            "yearsOfData": df['date'].dt.year.nunique()
        }

    def _empty_patterns(self) -> Dict[str, Any]:
        """Return empty patterns when no data available."""
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return {
            "monthlyPatterns": [{"month": m, "avgSermons": 0} for m in month_names],
            "dailyPatterns": [{"day": d, "sermons": 0} for d in
                              ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']],
            "busiestMonth": "Unknown",
            "quietestMonth": "Unknown",
            "locationFrequency": [],
            "totalSermons": 0,
            "yearsOfData": 0
        }

    def _get_location_frequency(self, df: pd.DataFrame) -> List[Dict]:
        """Get frequency of sermons by location."""
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

        loc_counts = df['location'].value_counts()
        return [{"location": loc, "count": int(count)} for loc, count in loc_counts.items()]

    def _build_rag_context(self, patterns: Dict, upcoming: Dict, health_score: int) -> str:
        """Build context string for RAG prompt."""
        now = datetime.now()

        context = f"""
MINISTRY PLANNING CONTEXT FOR APOSTLE NARCISSE MAJILA:

Date: {now.strftime('%Y-%m-%d')}
Planning for: {upcoming['nextMonth']['monthName']} {upcoming['nextMonth']['year']}

CURRENT STATUS:
- Health Score: {health_score}/100
- Predicted sermons next month: {upcoming['nextMonth']['predictedSermons']}
- Predicted trips next month: {upcoming['nextMonth']['predictedTrips']}
- Historically busy days in {upcoming['nextMonth']['monthName']}: {', '.join(upcoming['nextMonth']['busyDays']) if upcoming['nextMonth']['busyDays'] else 'None identified'}

HISTORICAL PATTERNS:
- Total sermons in database: {patterns['totalSermons']}
- Years of data: {patterns['yearsOfData']}
- Busiest month historically: {patterns['busiestMonth']}
- Quietest month historically: {patterns['quietestMonth']}

AVERAGE SERMONS PER MONTH:
{chr(10).join([f"- {p['month']}: {p['avgSermons']} sermons" for p in patterns['monthlyPatterns']])}

SERMONS BY DAY OF WEEK:
{chr(10).join([f"- {p['day']}: {p['sermons']} sermons" for p in patterns['dailyPatterns']])}

LOCATION FREQUENCY:
{chr(10).join([f"- {l['location']}: {l['count']} sermons" for l in patterns['locationFrequency'][:5]])}

Based on this data, provide planning recommendations for the upcoming month and beyond.
"""
        return context

    def generate_planning_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive planning report using AI.
        Falls back to rule-based report if Ollama unavailable.
        """
        patterns = self.get_historical_patterns()
        upcoming = self.get_upcoming_predictions()
        health_score = upcoming['nextMonth']['healthScore']

        # Check Ollama availability
        ollama_status = ollama_service.check_availability_sync()

        if ollama_status.get('available'):
            # Generate AI report
            context = self._build_rag_context(patterns, upcoming, health_score)
            prompt = f"{context}\n\nGenerate a planning report with trip recommendations, meeting suggestions, rest windows, and high-demand warnings."

            result = ollama_service.generate_json(
                prompt=prompt,
                system_prompt=self.PLANNER_SYSTEM_PROMPT,
                temperature=0.4
            )

            if result.get('success') and result.get('data'):
                ai_report = result['data']
                return {
                    "generatedAt": datetime.now().isoformat(),
                    "upcomingOverview": ai_report.get('upcomingOverview', ''),
                    "tripRecommendations": ai_report.get('tripRecommendations', []),
                    "meetingSuggestions": ai_report.get('meetingSuggestions', []),
                    "restWindows": ai_report.get('restWindows', []),
                    "highDemandWarnings": ai_report.get('highDemandWarnings', []),
                    "patterns": patterns,
                    "upcoming": upcoming,
                    "ollamaAvailable": True,
                    "aiGenerated": True
                }

        # Fallback to rule-based report
        return self._generate_fallback_report(patterns, upcoming, health_score, ollama_status.get('available', False))

    def _generate_fallback_report(self, patterns: Dict, upcoming: Dict, health_score: int, ollama_available: bool) -> Dict[str, Any]:
        """Generate rule-based report when AI is unavailable."""
        now = datetime.now()
        next_month = upcoming['nextMonth']['monthName']

        # Generate overview
        overview = f"Based on historical patterns, {next_month} typically sees "
        monthly_patterns = {p['month']: p['avgSermons'] for p in patterns['monthlyPatterns']}
        avg = monthly_patterns.get(next_month[:3], 0)
        overview += f"approximately {avg} sermons. "

        if patterns['busiestMonth'] == next_month[:3]:
            overview += f"This is historically the busiest month for ministry activities."
        elif patterns['quietestMonth'] == next_month[:3]:
            overview += f"This is historically a quieter month, good for rest and planning."

        # Trip recommendations
        trip_recommendations = []

        # Find locations that haven't been visited recently
        location_freq = patterns.get('locationFrequency', [])
        if location_freq:
            # Suggest visiting less-frequent locations
            for loc in location_freq:
                if loc['location'] not in ['Pretoria', 'Unknown'] and loc['count'] > 0:
                    trip_recommendations.append({
                        "destination": loc['location'],
                        "suggestedPeriod": f"Mid-{next_month}",
                        "reason": f"Regular ministry connection ({loc['count']} previous visits)",
                        "priority": "medium"
                    })
                    if len(trip_recommendations) >= 2:
                        break

        if not trip_recommendations:
            trip_recommendations.append({
                "destination": "Kinshasa",
                "suggestedPeriod": f"Mid-{next_month}",
                "reason": "Key ministry location in DRC",
                "priority": "medium"
            })

        # Meeting suggestions based on day patterns
        daily_patterns = {p['day']: p['sermons'] for p in patterns['dailyPatterns']}
        quietest_day = min(daily_patterns, key=daily_patterns.get) if daily_patterns else "Tuesday"

        meeting_suggestions = [
            {
                "type": "Team Planning Meeting",
                "suggestedDay": quietest_day,
                "suggestedTime": "Morning",
                "reason": f"Historically lowest sermon activity on {quietest_day}s"
            },
            {
                "type": "Ministry Review",
                "suggestedDay": "First Monday of month",
                "suggestedTime": "Afternoon",
                "reason": "Start of month allows full planning cycle"
            }
        ]

        # Rest windows
        rest_windows = []
        next_month_num = upcoming['nextMonth']['month']
        year = upcoming['nextMonth']['year']

        # Suggest rest after first week
        rest_windows.append({
            "start": f"{year}-{next_month_num:02d}-08",
            "end": f"{year}-{next_month_num:02d}-10",
            "type": "rest",
            "note": "Mid-week recovery period"
        })

        # If health score is high, suggest more rest
        if health_score > 60:
            rest_windows.append({
                "start": f"{year}-{next_month_num:02d}-20",
                "end": f"{year}-{next_month_num:02d}-25",
                "type": "rest",
                "note": "Extended rest recommended due to current workload"
            })

        # High demand warnings
        high_demand_warnings = []

        if patterns['busiestMonth'] in [patterns['monthlyPatterns'][i]['month'] for i in range(len(patterns['monthlyPatterns']))]:
            busiest_idx = next((i for i, p in enumerate(patterns['monthlyPatterns']) if p['month'] == patterns['busiestMonth']), None)
            if busiest_idx is not None:
                high_demand_warnings.append(f"{patterns['busiestMonth']} is historically the busiest month - plan rest beforehand")

        if upcoming['nextMonth']['predictedSermons'] > 4:
            high_demand_warnings.append(f"Forecast predicts {upcoming['nextMonth']['predictedSermons']} sermons next month - above average")

        # Add Easter/Christmas warnings if applicable
        if next_month_num in [3, 4]:  # March/April (Easter)
            high_demand_warnings.append("Easter season approaching - expect increased demand")
        if next_month_num == 12:
            high_demand_warnings.append("December services typically increase around Christmas")

        if not high_demand_warnings:
            high_demand_warnings.append("No unusual high-demand periods identified for next month")

        return {
            "generatedAt": datetime.now().isoformat(),
            "upcomingOverview": overview,
            "tripRecommendations": trip_recommendations,
            "meetingSuggestions": meeting_suggestions,
            "restWindows": rest_windows,
            "highDemandWarnings": high_demand_warnings,
            "patterns": patterns,
            "upcoming": upcoming,
            "ollamaAvailable": ollama_available,
            "aiGenerated": False
        }
