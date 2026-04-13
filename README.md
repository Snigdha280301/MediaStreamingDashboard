# Real-Time Media Intelligence Pipeline

A real-time data streaming and AI insights pipeline pulling continuously from TMDB, validating data with Great Expectations, storing in Delta Lake (Databricks), transforming with dbt, and utilizing a LangGraph multi-agent system (tracked by MLflow) to deliver predictive insights to Power BI dashboards.

## Stack Overview
- **Data Source:** TMDB Official API
- **Data Quality:** Great Expectations
- **Storage:** Databricks Delta Lake
- **Transformation:** dbt (dbt-databricks)
- **AI/Agents:** LangGraph
- **Experiment Tracking:** MLflow
- **Visualization:** Power BI

## Setup Instructions

1. **Environment Initialization:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

2. **Run Pipeline Components:**
   (Execution commands for scraping, tracking, and transformation will be run via respective scripts like main.py when built out.)
