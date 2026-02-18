# api-ingestion
A little playing around some data pipelines

Installation notes are down below.
Important: Do not mind PostgreSQL sections, I used them as a test as I do not have a GCP project set up for my private use, unless you want to do classic .
Important: This version of script does not really save JSON files into GDrive, just emulates saving mechanism for the sake of preserving disk space in case of excessive loads.

ADR-0: Use a mock API, not the GA4 native integration with BigQuery.
    Rationale: Usually in production, in cases like this we should use the Occam's razor principle and do not increase IT complexity without strong neccessity. This means, that if same data as the data from this mock API is available for integration directly from GA4 feed, it is architecturally advised to use native integration between GA4 and GCP and ingest events directly without creating an additional potential breaking point.
    Implication: Since this exersise is done solely for tech. skills assessment, we assume that in this situation we have chosen from two comparable solutions options the scenario with leveraging an API as data source due to some random reasons wich we will not further consider. Just for the sake of keeping a historical Architectuire Decision Record - choosing another (recommended) option with native integration would affect the cost, the data model and overall downstream pipeline design, which we do not consider in the course of this evaluation.

ADR-1: Schema design - use semi-nested structure with STRUCT and REPEATED.
    Rationale: We preserve nested GA structure using native BigQuery STRUCT and REPEATED. This ensures minimal transform loss, supports schema evolution (to some degree) and keeps structures cost efficient, because:
        1. Pure bronze (untransformed) is supposed to be our GDrive-dumped JSON files, and this layer is also a bronze layer (pre-processed raw data).
        2. Approach supports SQL queries for data quality issue investigations and disaster resolve.
        3. dbt-ready.
    Implication: since this is a combination of a pure raw (files) and pre-processed (BQ bronze) layers - no analytical downstream (like Power BI, quick business data analytics) is allowed. We will create a modelled (gold, analytics-ready layer in the step with dbt).

ADR-2: Additional metadata - the minimal enchancement is:
    1. session_pk - determinated Primary Key for a session for a possible future parralelization/idempotency issue investigation/resolving. We will probably not use this in this case study.
    Important: to make this script production-ready, session_pk should be used for duplicates handling, but a duplicate resolving strategy will also be required: keeping duplicates vs overwriting duplicates.
    2. load_timestamp
    3. source_date
    4. source_gdrive_path

Installation and running the script:
1. Clone the repository into the environment where you have Python of version >=3.10.0 installed.
2. Ensure you have credentials for Google Drive (gdrive path) and BQ connection (project, dataset, key).
3. Run command from the terminal (configure desired start-date and end-date within script call command):
  python fetch_api_data.py \
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