"""
Ministry Forecasting Module - XGBoost Models for 2026 Predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


class MinistryForecaster:
    """XGBoost-based forecasting for ministry activities"""

    def __init__(self):
        self.sermon_model = None
        self.trip_model = None
        self.sermon_metrics = {}
        self.trip_metrics = {}
        self.last_trained = None
        self.training_samples = 0

    def prepare_monthly_data(self, videos_df: pd.DataFrame) -> pd.DataFrame:
        """Convert video data to monthly aggregations"""
        # Parse upload dates
        df = videos_df.copy()
        df['upload_date'] = pd.to_datetime(df['upload_date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['upload_date'])

        # Create year-month column
        df['year_month'] = df['upload_date'].dt.to_period('M')

        # Aggregate by month
        monthly = df.groupby('year_month').agg({
            'video_id': 'count',
            'duration': 'sum',
            'view_count': 'sum'
        }).reset_index()

        monthly.columns = ['year_month', 'sermon_count', 'total_duration', 'total_views']
        monthly['date'] = monthly['year_month'].dt.to_timestamp()

        return monthly.sort_values('date').reset_index(drop=True)

    def create_features(self, df: pd.DataFrame, target_col: str = 'sermon_count') -> pd.DataFrame:
        """Create time series features for XGBoost"""
        data = df.copy()

        # Time-based features
        data['month'] = data['date'].dt.month
        data['quarter'] = data['date'].dt.quarter
        data['year'] = data['date'].dt.year

        # Cyclical encoding for month (captures seasonality better)
        data['month_sin'] = np.sin(2 * np.pi * data['month'] / 12)
        data['month_cos'] = np.cos(2 * np.pi * data['month'] / 12)

        # Lag features
        data['lag_1'] = data[target_col].shift(1)
        data['lag_2'] = data[target_col].shift(2)
        data['lag_3'] = data[target_col].shift(3)
        data['lag_6'] = data[target_col].shift(6)
        data['lag_12'] = data[target_col].shift(12)

        # Rolling statistics
        data['rolling_mean_3'] = data[target_col].rolling(window=3, min_periods=1).mean().shift(1)
        data['rolling_mean_6'] = data[target_col].rolling(window=6, min_periods=1).mean().shift(1)
        data['rolling_mean_12'] = data[target_col].rolling(window=12, min_periods=1).mean().shift(1)
        data['rolling_std_3'] = data[target_col].rolling(window=3, min_periods=1).std().shift(1)
        data['rolling_std_12'] = data[target_col].rolling(window=12, min_periods=1).std().shift(1)

        # Trend
        data['trend'] = range(len(data))

        # Year-over-year features
        data['yoy_diff'] = data[target_col] - data[target_col].shift(12)

        return data

    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns for modeling"""
        return [
            'month', 'quarter', 'month_sin', 'month_cos',
            'lag_1', 'lag_2', 'lag_3', 'lag_6', 'lag_12',
            'rolling_mean_3', 'rolling_mean_6', 'rolling_mean_12',
            'rolling_std_3', 'rolling_std_12', 'trend'
        ]

    def train_sermon_model(self, monthly_data: pd.DataFrame) -> Dict:
        """Train XGBoost model for sermon count predictions"""
        if not XGBOOST_AVAILABLE:
            return {"error": "XGBoost not available"}

        # Create features
        data = self.create_features(monthly_data, 'sermon_count')

        # Remove rows with NaN (due to lag features)
        data = data.dropna()

        if len(data) < 12:
            return {"error": "Not enough data for training (need at least 12 months)"}

        features = self.get_feature_columns()
        X = data[features]
        y = data['sermon_count']

        # Train model
        self.sermon_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            min_child_weight=3,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='reg:squarederror',
            random_state=42
        )

        self.sermon_model.fit(X, y)

        # Calculate metrics on training data
        predictions = self.sermon_model.predict(X)
        mae = mean_absolute_error(y, predictions)
        rmse = np.sqrt(mean_squared_error(y, predictions))

        self.sermon_metrics = {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'samples': len(data)
        }

        self.training_samples = len(data)
        self.last_trained = datetime.now().isoformat()

        # Store last known values for prediction
        self._last_sermon_data = data.iloc[-12:].copy()
        self._last_sermon_values = monthly_data['sermon_count'].values[-12:].tolist()

        return self.sermon_metrics

    def predict_sermons_2026(self, monthly_data: pd.DataFrame) -> List[Dict]:
        """Generate monthly sermon predictions for 2026"""
        if self.sermon_model is None:
            self.train_sermon_model(monthly_data)

        if self.sermon_model is None:
            return []

        predictions = []

        # Get historical data for lag features
        data = self.create_features(monthly_data, 'sermon_count')
        last_values = monthly_data['sermon_count'].values.tolist()

        # Use rolling values for prediction
        rolling_values = last_values[-12:] if len(last_values) >= 12 else last_values

        for month in range(1, 13):
            # Create feature row for prediction
            trend_val = len(monthly_data) + month

            # Calculate lag values
            lag_1 = rolling_values[-1] if len(rolling_values) >= 1 else 3
            lag_2 = rolling_values[-2] if len(rolling_values) >= 2 else 3
            lag_3 = rolling_values[-3] if len(rolling_values) >= 3 else 3
            lag_6 = rolling_values[-6] if len(rolling_values) >= 6 else 3
            lag_12 = rolling_values[-12] if len(rolling_values) >= 12 else 3

            # Rolling statistics
            rolling_mean_3 = np.mean(rolling_values[-3:]) if len(rolling_values) >= 3 else 3
            rolling_mean_6 = np.mean(rolling_values[-6:]) if len(rolling_values) >= 6 else 3
            rolling_mean_12 = np.mean(rolling_values[-12:]) if len(rolling_values) >= 12 else 3
            rolling_std_3 = np.std(rolling_values[-3:]) if len(rolling_values) >= 3 else 1
            rolling_std_12 = np.std(rolling_values[-12:]) if len(rolling_values) >= 12 else 1

            features = {
                'month': month,
                'quarter': (month - 1) // 3 + 1,
                'month_sin': np.sin(2 * np.pi * month / 12),
                'month_cos': np.cos(2 * np.pi * month / 12),
                'lag_1': lag_1,
                'lag_2': lag_2,
                'lag_3': lag_3,
                'lag_6': lag_6,
                'lag_12': lag_12,
                'rolling_mean_3': rolling_mean_3,
                'rolling_mean_6': rolling_mean_6,
                'rolling_mean_12': rolling_mean_12,
                'rolling_std_3': rolling_std_3,
                'rolling_std_12': rolling_std_12,
                'trend': trend_val
            }

            X_pred = pd.DataFrame([features])
            pred = self.sermon_model.predict(X_pred)[0]
            pred = max(0, round(pred))  # Ensure non-negative

            # Add prediction to rolling values for next iteration
            rolling_values.append(pred)
            if len(rolling_values) > 24:
                rolling_values = rolling_values[-24:]

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            predictions.append({
                'period': f'2026-{month:02d}',
                'month': month_names[month - 1],
                'value': int(pred),
                'lower': max(0, int(pred - self.sermon_metrics.get('rmse', 2))),
                'upper': int(pred + self.sermon_metrics.get('rmse', 2))
            })

        return predictions

    def prepare_trip_data(self, videos_df: pd.DataFrame, location_changes: pd.DataFrame = None) -> pd.DataFrame:
        """Prepare trip data from location changes"""
        df = videos_df.copy()
        df['upload_date'] = pd.to_datetime(df['upload_date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['upload_date'])
        df = df.sort_values('upload_date')

        # Extract location from title/channel (simplified)
        def extract_location(row):
            text = f"{row.get('channel_name', '')} {row.get('title', '')}".lower()
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
            for loc, keywords in locations.items():
                for kw in keywords:
                    if kw in text:
                        return loc
            return 'Pretoria'  # Default home base

        df['location'] = df.apply(extract_location, axis=1)
        df['year_month'] = df['upload_date'].dt.to_period('M')

        # Count unique locations per month (trips = location changes)
        monthly_trips = df.groupby('year_month').agg({
            'location': lambda x: len(x.unique()) - 1  # -1 because staying at home isn't a trip
        }).reset_index()

        monthly_trips.columns = ['year_month', 'trips']
        monthly_trips['trips'] = monthly_trips['trips'].clip(lower=0)
        monthly_trips['date'] = monthly_trips['year_month'].dt.to_timestamp()

        return monthly_trips.sort_values('date').reset_index(drop=True)

    def train_trip_model(self, trip_data: pd.DataFrame) -> Dict:
        """Train XGBoost model for trip predictions"""
        if not XGBOOST_AVAILABLE:
            return {"error": "XGBoost not available"}

        if len(trip_data) < 12:
            return {"error": "Not enough trip data"}

        data = self.create_features(trip_data, 'trips')
        data = data.dropna()

        if len(data) < 6:
            return {"error": "Not enough data after feature creation"}

        features = self.get_feature_columns()
        X = data[features]
        y = data['trips']

        self.trip_model = xgb.XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            objective='reg:squarederror',
            random_state=42
        )

        self.trip_model.fit(X, y)

        predictions = self.trip_model.predict(X)
        mae = mean_absolute_error(y, predictions)
        rmse = np.sqrt(mean_squared_error(y, predictions))

        self.trip_metrics = {
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'samples': len(data)
        }

        self._last_trip_values = trip_data['trips'].values[-12:].tolist()

        return self.trip_metrics

    def predict_trips_2026(self, trip_data: pd.DataFrame) -> List[Dict]:
        """Generate monthly trip predictions for 2026"""
        if self.trip_model is None:
            self.train_trip_model(trip_data)

        if self.trip_model is None:
            return []

        predictions = []
        rolling_values = trip_data['trips'].values.tolist()[-12:] if len(trip_data) >= 12 else trip_data['trips'].values.tolist()

        for month in range(1, 13):
            trend_val = len(trip_data) + month

            lag_1 = rolling_values[-1] if len(rolling_values) >= 1 else 1
            lag_2 = rolling_values[-2] if len(rolling_values) >= 2 else 1
            lag_3 = rolling_values[-3] if len(rolling_values) >= 3 else 1
            lag_6 = rolling_values[-6] if len(rolling_values) >= 6 else 1
            lag_12 = rolling_values[-12] if len(rolling_values) >= 12 else 1

            rolling_mean_3 = np.mean(rolling_values[-3:]) if len(rolling_values) >= 3 else 1
            rolling_mean_6 = np.mean(rolling_values[-6:]) if len(rolling_values) >= 6 else 1
            rolling_mean_12 = np.mean(rolling_values[-12:]) if len(rolling_values) >= 12 else 1
            rolling_std_3 = np.std(rolling_values[-3:]) if len(rolling_values) >= 3 else 0.5
            rolling_std_12 = np.std(rolling_values[-12:]) if len(rolling_values) >= 12 else 0.5

            features = {
                'month': month,
                'quarter': (month - 1) // 3 + 1,
                'month_sin': np.sin(2 * np.pi * month / 12),
                'month_cos': np.cos(2 * np.pi * month / 12),
                'lag_1': lag_1,
                'lag_2': lag_2,
                'lag_3': lag_3,
                'lag_6': lag_6,
                'lag_12': lag_12,
                'rolling_mean_3': rolling_mean_3,
                'rolling_mean_6': rolling_mean_6,
                'rolling_mean_12': rolling_mean_12,
                'rolling_std_3': rolling_std_3,
                'rolling_std_12': rolling_std_12,
                'trend': trend_val
            }

            X_pred = pd.DataFrame([features])
            pred = self.trip_model.predict(X_pred)[0]
            pred = max(0, round(pred))

            rolling_values.append(pred)
            if len(rolling_values) > 24:
                rolling_values = rolling_values[-24:]

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            predictions.append({
                'period': f'2026-{month:02d}',
                'month': month_names[month - 1],
                'trips': int(pred)
            })

        return predictions

    def get_historical_data(self, monthly_data: pd.DataFrame) -> List[Dict]:
        """Get historical sermon counts for visualization"""
        return [
            {
                'period': str(row['year_month']),
                'value': int(row['sermon_count']),
                'duration': round(row['total_duration'] / 3600, 1) if row['total_duration'] else 0
            }
            for _, row in monthly_data.iterrows()
        ]

    def get_model_status(self) -> Dict:
        """Get current model training status"""
        return {
            'sermonModel': {
                'trained': self.sermon_model is not None,
                'lastUpdated': self.last_trained,
                'samples': self.sermon_metrics.get('samples', 0),
                'mae': self.sermon_metrics.get('mae'),
                'rmse': self.sermon_metrics.get('rmse')
            },
            'tripModel': {
                'trained': self.trip_model is not None,
                'samples': self.trip_metrics.get('samples', 0),
                'mae': self.trip_metrics.get('mae'),
                'rmse': self.trip_metrics.get('rmse')
            },
            'xgboostAvailable': XGBOOST_AVAILABLE
        }


# Global forecaster instance
forecaster = MinistryForecaster()
