"""
Power BI Dashboard Setup for Predictive Maintenance
Creates data exports and dashboard configuration for Power BI
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class PowerBIDashboardSetup:
    def __init__(self):
        self.dashboard_config = {}
        
    def create_kpi_data(self, df, model_results):
        """Create KPI data for Power BI dashboard"""
        print("Creating KPI data for Power BI...")
        
        # Calculate KPIs
        kpis = {
            'total_machines': int(df['machine_id'].nunique()),
            'total_records': int(len(df)),
            'failure_rate': float(df['failure'].mean()),
            'model_accuracy': float(model_results['accuracy']),
            'model_auc': float(model_results['auc_score']),
            'model_f1': float(model_results['f1_score']),
            'predicted_failures': int(model_results['predictions'].sum()),
            'actual_failures': int(df['failure'].sum()),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Machine-level KPIs
        machine_kpis = df.groupby('machine_id').agg({
            'failure': ['sum', 'mean', 'count'],
            'temperature': 'mean',
            'vibration': 'mean',
            'pressure': 'mean',
            'speed': 'mean',
            'product_quality': 'mean'
        }).round(3)
        
        machine_kpis.columns = ['total_failures', 'failure_rate', 'total_records', 
                               'avg_temperature', 'avg_vibration', 'avg_pressure', 
                               'avg_speed', 'avg_quality']
        machine_kpis = machine_kpis.reset_index()
        
        # Daily KPIs
        daily_kpis = df.groupby('date').agg({
            'failure': ['sum', 'mean'],
            'machine_id': 'nunique',
            'temperature': 'mean',
            'vibration': 'mean',
            'product_quality': 'mean'
        }).round(3)
        
        daily_kpis.columns = ['daily_failures', 'daily_failure_rate', 'active_machines',
                            'avg_temperature', 'avg_vibration', 'avg_quality']
        daily_kpis = daily_kpis.reset_index()
        
        return kpis, machine_kpis, daily_kpis
    
    def create_maintenance_schedule(self, df, model_results):
        """Create maintenance schedule based on predictions"""
        print("Creating maintenance schedule...")
        
        # Get predictions and probabilities
        predictions = model_results['predictions']
        probabilities = model_results['probabilities']
        
        # Create maintenance recommendations
        maintenance_data = df.copy()
        maintenance_data['predicted_failure'] = predictions
        maintenance_data['failure_probability'] = probabilities
        
        # Define maintenance priority based on probability
        maintenance_data['maintenance_priority'] = np.where(
            maintenance_data['failure_probability'] >= 0.8, 'Critical',
            np.where(maintenance_data['failure_probability'] >= 0.6, 'High',
                    np.where(maintenance_data['failure_probability'] >= 0.4, 'Medium', 'Low'))
        )
        
        # Create maintenance schedule
        maintenance_schedule = maintenance_data[
            maintenance_data['predicted_failure'] == 1
        ][['machine_id', 'date', 'failure_probability', 'maintenance_priority']].copy()
        
        maintenance_schedule['recommended_action'] = np.where(
            maintenance_schedule['maintenance_priority'] == 'Critical', 'Immediate Maintenance',
            np.where(maintenance_schedule['maintenance_priority'] == 'High', 'Schedule Maintenance',
                    'Monitor Closely')
        )
        
        maintenance_schedule = maintenance_schedule.sort_values('failure_probability', ascending=False)
        
        return maintenance_schedule
    
    def create_export_files(self, df, model_results):
        """Create files for Power BI import"""
        print("Creating export files for Power BI...")
        
        # Create KPI data
        kpis, machine_kpis, daily_kpis = self.create_kpi_data(df, model_results)
        
        # Create maintenance schedule
        maintenance_schedule = self.create_maintenance_schedule(df, model_results)
        
        # Export to CSV files
        machine_kpis.to_csv('dashboard/machine_kpis.csv', index=False)
        daily_kpis.to_csv('dashboard/daily_kpis.csv', index=False)
        maintenance_schedule.to_csv('dashboard/maintenance_schedule.csv', index=False)
        
        # Save KPIs as JSON
        with open('dashboard/kpis.json', 'w') as f:
            json.dump(kpis, f, indent=2)
        
        # Create Power BI configuration
        self.create_powerbi_config(kpis)
        
        print("Export files created successfully!")
        print("Files created:")
        print("- dashboard/machine_kpis.csv")
        print("- dashboard/daily_kpis.csv") 
        print("- dashboard/maintenance_schedule.csv")
        print("- dashboard/kpis.json")
        print("- dashboard/powerbi_config.json")
        
        return kpis, machine_kpis, daily_kpis, maintenance_schedule
    
    def create_powerbi_config(self, kpis):
        """Create Power BI dashboard configuration"""
        config = {
            "dashboard_title": "Predictive Maintenance Dashboard",
            "description": "Real-time monitoring of manufacturing equipment with AI-powered failure predictions",
            "data_sources": [
                {
                    "name": "Machine KPIs",
                    "file": "machine_kpis.csv",
                    "type": "CSV",
                    "description": "Machine-level performance metrics"
                },
                {
                    "name": "Daily KPIs", 
                    "file": "daily_kpis.csv",
                    "type": "CSV",
                    "description": "Daily aggregated performance metrics"
                },
                {
                    "name": "Maintenance Schedule",
                    "file": "maintenance_schedule.csv", 
                    "type": "CSV",
                    "description": "AI-recommended maintenance actions"
                },
                {
                    "name": "KPIs Summary",
                    "file": "kpis.json",
                    "type": "JSON",
                    "description": "Overall system KPIs"
                }
            ],
            "visualizations": [
                {
                    "title": "Overall System Health",
                    "type": "KPI Cards",
                    "metrics": ["model_accuracy", "failure_rate", "total_machines"],
                    "description": "Key performance indicators for the entire system"
                },
                {
                    "title": "Machine Performance Overview",
                    "type": "Table",
                    "data_source": "machine_kpis",
                    "description": "Detailed performance metrics for each machine"
                },
                {
                    "title": "Daily Failure Trends",
                    "type": "Line Chart",
                    "data_source": "daily_kpis",
                    "x_axis": "date",
                    "y_axis": "daily_failures",
                    "description": "Trend of failures over time"
                },
                {
                    "title": "Maintenance Priority Matrix",
                    "type": "Scatter Plot",
                    "data_source": "maintenance_schedule",
                    "x_axis": "failure_probability",
                    "y_axis": "machine_id",
                    "color": "maintenance_priority",
                    "description": "Machines requiring maintenance based on failure probability"
                },
                {
                    "title": "Sensor Readings Distribution",
                    "type": "Histogram",
                    "data_source": "machine_kpis",
                    "metrics": ["avg_temperature", "avg_vibration", "avg_pressure"],
                    "description": "Distribution of sensor readings across machines"
                },
                {
                    "title": "Quality vs Performance",
                    "type": "Scatter Plot",
                    "data_source": "machine_kpis",
                    "x_axis": "avg_quality",
                    "y_axis": "failure_rate",
                    "description": "Relationship between product quality and failure rates"
                }
            ],
            "refresh_settings": {
                "auto_refresh": True,
                "refresh_interval": "1 hour",
                "data_source_update": "daily"
            },
            "alerts": [
                {
                    "name": "High Failure Probability",
                    "condition": "failure_probability >= 0.8",
                    "action": "Send email notification",
                    "description": "Alert when any machine has high failure probability"
                },
                {
                    "name": "Model Accuracy Drop",
                    "condition": "model_accuracy < 0.90",
                    "action": "Send email notification", 
                    "description": "Alert when model accuracy drops below 90%"
                }
            ],
            "last_updated": kpis['last_updated']
        }
        
        with open('dashboard/powerbi_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return config

def main():
    """Main function to set up Power BI dashboard"""
    print("Setting up Power BI Dashboard...")
    
    # Load processed data
    df = pd.read_csv('data/processed/manufacturing_data_processed.csv')
    
    # Load model results (simulate for demo)
    model_results = {
        'accuracy': 0.95,  # Target accuracy
        'auc_score': 0.85,
        'f1_score': 0.75,
        'predictions': np.random.choice([0, 1], size=len(df), p=[0.93, 0.07]),
        'probabilities': np.random.uniform(0, 1, size=len(df))
    }
    
    # Initialize dashboard setup
    dashboard_setup = PowerBIDashboardSetup()
    
    # Create export files
    kpis, machine_kpis, daily_kpis, maintenance_schedule = dashboard_setup.create_export_files(df, model_results)
    
    print("\nPower BI Dashboard setup completed!")
    print("Next steps:")
    print("1. Import the CSV files into Power BI")
    print("2. Use the powerbi_config.json as a guide for creating visualizations")
    print("3. Set up automatic data refresh")
    print("4. Configure alerts for critical conditions")
    
    return dashboard_setup

if __name__ == "__main__":
    dashboard_setup = main()


