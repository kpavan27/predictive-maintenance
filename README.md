# Predictive maintenance for manufacturing

A data pipeline for machine-failure prediction on simulated sensor data: data generation, cleaning, feature engineering and a Power BI KPI layer.

> **Status: in progress.** The data and feature pipeline is in this repo. The model training and evaluation code is being cleaned up and added, so no model metrics are reported here yet.

## What's in the repo

| Path | What it does |
|---|---|
| `data/data_generator.py` | Simulates one year of daily readings for 50 machines across 5 machine types (18,250 machine-days). Failure probability depends on machine type, age and maintenance frequency; about 6.7% of days are failure days. To mimic real telemetry, about 5% of rows have one sensor reading blanked and 2% get an injected outlier. |
| `data/data_preprocessing.py` | Outlier capping (±3 SD), KNN imputation, per-machine rolling 7- and 30-day means and standard deviations, ratio features, lagged failure flags, univariate feature selection and scaling. |
| `dashboard/powerbi_dashboard_setup.py` | Builds the machine-level and system-level KPI tables a Power BI report reads (`powerbi_config.json`). |
| `run_project.py` | End-to-end runner. Its training step expects the `models/` code that is still being added, so for now run the two data scripts below directly. |

## Run it

```bash
pip install pandas numpy scikit-learn
python data/data_generator.py        # writes data/raw/manufacturing_data.csv
python data/data_preprocessing.py    # writes data/processed/
```

## Evaluation plan

The positive class is rare (~6.7% of days), so a model that always predicts "no failure" already scores about 93% accuracy. Accuracy is therefore not a useful headline metric here. The evaluation being added will report:

- PR-AUC, and recall at a fixed false-alarm budget, against that always-negative baseline
- time-based splits per machine, so rolling features never see the future
- a check that features derived from the failure label (such as lagged failure flags) can't leak the target

## Limitations

The data is simulated, so results will show whether the pipeline works, not how it performs on real equipment. A natural next step is to rerun it on the public [AI4I 2020 Predictive Maintenance dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).
