from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# -------------------------
# Default Arguments
# -------------------------

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=3),
}

# -------------------------
# DAG Definition
# -------------------------

with DAG(
    dag_id="etl_ga_sessions_pipeline",
    description="GA Sessions full pipeline: ingestion → silver → gold → dq",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 6,18 * * 3",  # 06:00 and 18:00 every Wednesday
    catchup=False,
    max_active_runs=1,
    tags=["ga", "bronze", "silver", "gold", "dbt"],
) as dag:

    # -----------------------------------
    # 1️⃣ INGESTION STEP
    # -----------------------------------

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
            --gdrive-path "gdrive://path-to-my-use-case-drive"
        """,
    )

    # -----------------------------------
    # 2️⃣ DBT SILVER TRANSFORMATIONS
    # -----------------------------------

    run_dbt_silver = BashOperator(
        task_id="run_dbt_silver",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        dbt run \
          --target prod \
          --select staging
        """,
    )

    # -----------------------------------
    # 3️⃣ DBT GOLD TRANSFORMATIONS
    # -----------------------------------

    run_dbt_gold = BashOperator(
        task_id="run_dbt_gold",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        dbt run \
          --target prod \
          --select marts
        """,
    )

    # -----------------------------------
    # 4️⃣ DBT DATA QUALITY TESTS
    # -----------------------------------

    run_dbt_tests = BashOperator(
        task_id="run_dbt_tests",
        bash_command="""
        cd /opt/airflow/dbt_project && \
        dbt test \
          --target prod
        """,
    )

    # -----------------------------------
    # DAG DEPENDENCIES
    # -----------------------------------

    run_ingestion >> run_dbt_silver >> run_dbt_gold >> run_dbt_tests