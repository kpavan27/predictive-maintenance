"""
Data Preprocessing for Predictive Maintenance
Handles data cleaning, feature engineering, and missing value imputation
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import KNNImputer
from sklearn.feature_selection import SelectKBest, f_classif
import warnings
warnings.filterwarnings('ignore')

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_selector = None
        self.imputer = KNNImputer(n_neighbors=5)
        
    def load_data(self, file_path):
        """Load the raw manufacturing data"""
        print(f"Loading data from {file_path}")
        df = pd.read_csv(file_path)
        print(f"Data shape: {df.shape}")
        print(f"Missing values: {df.isnull().sum().sum()}")
        return df
    
    def clean_data(self, df):
        """Clean the data by removing outliers and handling data types"""
        print("Cleaning data...")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date'])
        
        # Remove extreme outliers (beyond 3 standard deviations)
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        numeric_columns = [col for col in numeric_columns if col not in ['machine_id', 'failure']]
        
        for col in numeric_columns:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Cap outliers instead of removing them
                df[col] = df[col].clip(lower_bound, upper_bound)
        
        print("Data cleaning completed")
        return df
    
    def engineer_features(self, df):
        """Create new features for better model performance"""
        print("Engineering features...")
        
        # Sort by machine_id and date for rolling calculations
        df = df.sort_values(['machine_id', 'date'])
        
        # Rolling statistics for each machine
        numeric_cols = ['temperature', 'vibration', 'pressure', 'speed', 'power_consumption']
        
        for col in numeric_cols:
            if col in df.columns:
                # Rolling means (7-day window)
                df[f'{col}_mean_7d'] = df.groupby('machine_id')[col].rolling(window=7, min_periods=1).mean().reset_index(0, drop=True)
                
                # Rolling standard deviations (7-day window)
                df[f'{col}_std_7d'] = df.groupby('machine_id')[col].rolling(window=7, min_periods=1).std().reset_index(0, drop=True)
                
                # Rolling means (30-day window)
                df[f'{col}_mean_30d'] = df.groupby('machine_id')[col].rolling(window=30, min_periods=1).mean().reset_index(0, drop=True)
                
                # Change from previous day
                df[f'{col}_change'] = df.groupby('machine_id')[col].diff()
                
                # Rate of change
                df[f'{col}_rate_change'] = df.groupby('machine_id')[col].pct_change()
        
        # Machine-specific features
        df['days_since_last_maintenance'] = df.groupby('machine_id')['date'].diff().dt.days.fillna(0)
        
        # Operating efficiency
        df['efficiency'] = df['product_quality'] / (df['power_consumption'] + 1)
        
        # Temperature-pressure ratio (important for mechanical systems)
        df['temp_pressure_ratio'] = df['temperature'] / (df['pressure'] + 1)
        
        # Vibration-speed ratio (indicates mechanical stress)
        df['vib_speed_ratio'] = df['vibration'] / (df['speed'] + 1)
        
        # Cumulative operating hours
        df['cumulative_hours'] = df.groupby('machine_id')['operating_hours'].cumsum()
        
        # Days since installation (approximate)
        df['days_since_install'] = (df['date'] - df.groupby('machine_id')['date'].transform('min')).dt.days
        
        # Maintenance frequency encoding
        maintenance_map = {'High': 3, 'Medium': 2, 'Low': 1}
        df['maintenance_frequency_encoded'] = df['maintenance_frequency'].map(maintenance_map)
        
        # Machine type encoding
        if 'machine_type' not in self.label_encoders:
            self.label_encoders['machine_type'] = LabelEncoder()
        df['machine_type_encoded'] = self.label_encoders['machine_type'].fit_transform(df['machine_type'])
        
        # Seasonal features
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Failure indicators (lagged features)
        df['failure_lag_1'] = df.groupby('machine_id')['failure'].shift(1).fillna(0)
        df['failure_lag_7'] = df.groupby('machine_id')['failure'].shift(7).fillna(0)
        
        print(f"Feature engineering completed. New shape: {df.shape}")
        return df
    
    def handle_missing_values(self, df):
        """Handle missing values using KNN imputation"""
        print("Handling missing values...")
        
        # Separate numeric and categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        # Handle categorical missing values
        for col in categorical_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')
        
        # Handle numeric missing values with KNN imputation
        numeric_df = df[numeric_cols].copy()
        
        # Replace infinity values with NaN
        numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)
        
        if numeric_df.isnull().sum().sum() > 0:
            print(f"Imputing {numeric_df.isnull().sum().sum()} missing values...")
            imputed_data = self.imputer.fit_transform(numeric_df)
            df[numeric_cols] = imputed_data
        
        print("Missing value handling completed")
        return df
    
    def select_features(self, df, target_col='failure', k=30):
        """Select the most important features"""
        print(f"Selecting top {k} features...")
        
        # Prepare features and target
        feature_cols = [col for col in df.columns if col not in ['machine_id', 'date', 'failure', 'machine_type', 'maintenance_frequency']]
        X = df[feature_cols]
        y = df[target_col]
        
        # Remove any remaining non-numeric columns
        X = X.select_dtypes(include=[np.number])
        
        # Feature selection
        self.feature_selector = SelectKBest(score_func=f_classif, k=k)
        X_selected = self.feature_selector.fit_transform(X, y)
        
        # Get selected feature names
        selected_features = X.columns[self.feature_selector.get_support()].tolist()
        
        print(f"Selected features: {selected_features}")
        
        # Create final dataset
        final_df = df[['machine_id', 'date', 'failure'] + selected_features].copy()
        
        return final_df, selected_features
    
    def scale_features(self, df, feature_cols, fit=True):
        """Scale features for model training"""
        print("Scaling features...")
        
        if fit:
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            df[feature_cols] = self.scaler.transform(df[feature_cols])
        
        return df
    
    def preprocess_pipeline(self, file_path, target_col='failure'):
        """Complete preprocessing pipeline"""
        print("Starting data preprocessing pipeline...")
        
        # Load data
        df = self.load_data(file_path)
        
        # Clean data
        df = self.clean_data(df)
        
        # Engineer features
        df = self.engineer_features(df)
        
        # Handle missing values
        df = self.handle_missing_values(df)
        
        # Select features
        df, selected_features = self.select_features(df, target_col)
        
        # Scale features
        feature_cols = [col for col in selected_features if col not in ['machine_id', 'date', 'failure']]
        df = self.scale_features(df, feature_cols, fit=True)
        
        print(f"Preprocessing completed. Final shape: {df.shape}")
        return df, selected_features

def main():
    """Main preprocessing function"""
    preprocessor = DataPreprocessor()
    
    # Process the data
    df, selected_features = preprocessor.preprocess_pipeline('data/raw/manufacturing_data.csv')
    
    # Save processed data
    df.to_csv('data/processed/manufacturing_data_processed.csv', index=False)
    
    # Save feature list
    feature_df = pd.DataFrame({'feature': selected_features})
    feature_df.to_csv('data/processed/selected_features.csv', index=False)
    
    print("Processed data saved to data/processed/manufacturing_data_processed.csv")
    print("Selected features saved to data/processed/selected_features.csv")
    
    return df, selected_features

if __name__ == "__main__":
    df, features = main()
