from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# -------------------------
# Default Arguments
# -------------------------

default_args = {
    "owner": "api-ingestion",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=3),
}

# -------------------------
# DAG Definition
# -------------------------

with DAG(
    dag_id="etl_ga_sessions_ingestion",
    description="GA Sessions ingestion pipeline (API → BigQuery + PostgreSQL)",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="0 6,18 * * 3",  # 06:00 and 18:00 every Wednesday
    catchup=False,
    max_active_runs=1,
    tags=["ga", "bronze", "silver", "bigquery"],
) as dag:

    run_ingestion = BashOperator(
        task_id="run_ga_sessions_ingestion",
        bash_command="""
        python /opt/airflow/dags/scripts/data_pipeline.py \
          --url "https://your-API-URL" \
          --api-key "your-API-key" \
          --start-date 20160801 \
          --end-date 20170801 \
          --limit 100 \
          --output-dir "./raw_output" \
          \
          --bq-project "my-use-case-analytics-project" \
          --bq-dataset "my-use-case-bronze-layer" \
          --bq-table "ga_sessions_raw" \
          --bq-credentials "/home/user/keys/bq-service-account.json" \
          \
          --gdrive-path "gdrive://path-to-my-use-case-drive" \
        """,
    )

    run_ingestion