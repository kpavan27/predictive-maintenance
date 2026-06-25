"""
Synthetic Manufacturing Equipment Data Generator
Generates realistic sensor data with failure patterns for predictive maintenance
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ManufacturingDataGenerator:
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        
    def generate_equipment_data(self, n_machines=50, days=365):
        """Generate comprehensive manufacturing equipment data"""
        
        data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for machine_id in range(1, n_machines + 1):
            machine_data = self._generate_machine_data(machine_id, start_date, days)
            data.extend(machine_data)
            
        df = pd.DataFrame(data)
        return df
    
    def _generate_machine_data(self, machine_id, start_date, days):
        """Generate data for a single machine"""
        
        # Machine characteristics
        machine_type = random.choice(['Conveyor', 'Press', 'Welder', 'CNC', 'Assembly'])
        age_years = random.uniform(1, 15)
        maintenance_frequency = random.choice(['High', 'Medium', 'Low'])
        
        # Failure probability based on machine characteristics
        base_failure_rate = self._get_base_failure_rate(machine_type, age_years, maintenance_frequency)
        
        machine_data = []
        current_date = start_date
        
        # Generate daily data
        for day in range(days):
            # Determine if failure occurs
            failure_prob = base_failure_rate + np.random.normal(0, 0.01)
            failure_prob = max(0, min(1, failure_prob))
            
            # Generate sensor readings
            sensor_data = self._generate_sensor_readings(machine_type, age_years, failure_prob)
            
            # Add failure flag
            sensor_data['machine_id'] = machine_id
            sensor_data['machine_type'] = machine_type
            sensor_data['age_years'] = age_years
            sensor_data['maintenance_frequency'] = maintenance_frequency
            sensor_data['date'] = current_date
            sensor_data['failure'] = 1 if random.random() < failure_prob else 0
            
            machine_data.append(sensor_data)
            current_date += timedelta(days=1)
            
        return machine_data
    
    def _get_base_failure_rate(self, machine_type, age_years, maintenance_frequency):
        """Calculate base failure rate based on machine characteristics"""
        
        # Base rates by machine type
        type_rates = {
            'Conveyor': 0.02,
            'Press': 0.05,
            'Welder': 0.08,
            'CNC': 0.03,
            'Assembly': 0.04
        }
        
        # Age factor (older machines fail more)
        age_factor = 1 + (age_years - 1) * 0.1
        
        # Maintenance factor
        maintenance_factors = {'High': 0.5, 'Medium': 1.0, 'Low': 1.5}
        
        base_rate = type_rates[machine_type] * age_factor * maintenance_factors[maintenance_frequency]
        return min(base_rate, 0.3)  # Cap at 30%
    
    def _generate_sensor_readings(self, machine_type, age_years, failure_prob):
        """Generate realistic sensor readings"""
        
        # Base values for different machine types
        base_values = {
            'Conveyor': {'temperature': 45, 'vibration': 2.5, 'pressure': 1.2, 'speed': 100},
            'Press': {'temperature': 65, 'vibration': 4.0, 'pressure': 8.5, 'speed': 50},
            'Welder': {'temperature': 120, 'vibration': 3.5, 'pressure': 2.1, 'speed': 30},
            'CNC': {'temperature': 55, 'vibration': 1.8, 'pressure': 1.5, 'speed': 200},
            'Assembly': {'temperature': 40, 'vibration': 2.0, 'pressure': 1.0, 'speed': 80}
        }
        
        base = base_values[machine_type]
        
        # Generate readings with failure indicators
        readings = {}
        
        # Temperature (increases before failure)
        temp_base = base['temperature']
        temp_noise = np.random.normal(0, 5)
        temp_failure_effect = failure_prob * 30  # Up to 30°C increase
        readings['temperature'] = temp_base + temp_noise + temp_failure_effect
        
        # Vibration (increases before failure)
        vib_base = base['vibration']
        vib_noise = np.random.normal(0, 0.3)
        vib_failure_effect = failure_prob * 3  # Up to 3x increase
        readings['vibration'] = max(0, vib_base + vib_noise + vib_failure_effect)
        
        # Pressure (varies by machine type)
        press_base = base['pressure']
        press_noise = np.random.normal(0, 0.2)
        press_failure_effect = failure_prob * 2  # Up to 2x increase
        readings['pressure'] = max(0, press_base + press_noise + press_failure_effect)
        
        # Speed (decreases before failure)
        speed_base = base['speed']
        speed_noise = np.random.normal(0, 10)
        speed_failure_effect = -failure_prob * 50  # Up to 50% decrease
        readings['speed'] = max(0, speed_base + speed_noise + speed_failure_effect)
        
        # Additional sensors
        readings['power_consumption'] = np.random.normal(100, 20) + failure_prob * 50
        readings['oil_level'] = max(0, min(100, np.random.normal(80, 10) - failure_prob * 30))
        readings['noise_level'] = np.random.normal(70, 5) + failure_prob * 20
        
        # Operating hours (cumulative)
        readings['operating_hours'] = np.random.uniform(8, 24)
        
        # Quality metrics
        readings['product_quality'] = max(0, min(100, np.random.normal(95, 3) - failure_prob * 20))
        
        return readings

def generate_dataset():
    """Generate the complete dataset"""
    generator = ManufacturingDataGenerator()
    
    print("Generating manufacturing equipment data...")
    df = generator.generate_equipment_data(n_machines=50, days=365)
    
    # Add some missing values (5% of data)
    missing_indices = np.random.choice(df.index, size=int(len(df) * 0.05), replace=False)
    missing_columns = ['temperature', 'vibration', 'pressure', 'oil_level']
    
    for idx in missing_indices:
        col = random.choice(missing_columns)
        df.loc[idx, col] = np.nan
    
    # Add some outliers
    outlier_indices = np.random.choice(df.index, size=int(len(df) * 0.02), replace=False)
    for idx in outlier_indices:
        col = random.choice(['temperature', 'vibration'])
        df.loc[idx, col] = df.loc[idx, col] * np.random.uniform(2, 5)
    
    print(f"Generated dataset with {len(df)} records")
    print(f"Failure rate: {df['failure'].mean():.2%}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    
    return df

if __name__ == "__main__":
    df = generate_dataset()
    df.to_csv('data/raw/manufacturing_data.csv', index=False)
    print("Dataset saved to data/raw/manufacturing_data.csv")
