This is a second step from running the standalone script to leveraging Airflow DAG and transforming the data with dbt.

To run DAG successfully, copy the file from Step 1-2 to the folder of the environment where Airflow is installed: data_pipeline.py -> /opt/airflow/dags/scripts/data_pipeline.py

Dbt models are exemplary, for illustration of a chain of transformations.

For cost assumptions please refer to the root README.md file.

Final physical data model:

    Staging (silver):
        stg_ga_sessions
        dq_ga_sessions
    Mart (gold):
        dim_device
        dim_geo
        dim_traffic_source
        fct_sessions
        dq_fct_sessions

Detailed DQ strategy and proposed initial checks are listed inj the Step 1-2's README.md, refer to it if necessary.

Quick recap of what we cover with DQ checks (just examples, list is extensible nearly infinitely according to analytics/business needs):

Observability:
    PK NOT NULL                     - idempotency enablement / integrity within a session / across sessions
    Hits/pageviews NULLs            - potential analytical metric calculations

Completeness:
    total_rows > 0                  - no gaps within time series / ingestion

Business rules:
    visits = 0 but pageviews > 0    - logical nonsence
    bounces > visits                - logical nonsence

ADR0: DQ Failure monitoring - DAG task should write a simple log into a file (could be rewritable for the sake of preserving disk space).
Rationale: in case BQ goes away during DQ checks execution by the DAG task, some traces of the run should be left for possible investigation.
Implication: this involves minimal disk space expenditure. Alternative option can be leveraging an Airflow log, if possible.

ADR1: General DQ Monitoring - results of DQ checks should go into BQ table.
Rationale: Results should be available for a quick access to execution outcome for quick analytics both manually and later on automatically.
Implication: It makes sense to later on create a monitoring dashboard, where all DQ results from ingestion pipelines should contribute into, without the need to do manual analytics or scrape logs.

ADR2: Runtime DAG/DQ Monitoring - results of overal execution might go into Slack/Telegram
Rationale: For critical production pipelines it might make sense to setup a messaging into Slack or Telegram using their APIs with critical step execution telemetry for quick response during night shifts or in general.
Implication: this will require additional bootstraping in DAG, which is not covered in this case study.

ADR3: General Data Lineage - it is recommended to leverage Dataplex universal catalog as GCP-native for automatic lineage from BQ schemas and beyond.
Rationale: it is recommended to use Dataplex for table to table and column to column data transformations, as this does not require additional programming.
Implication: Enabling Data Lineage API will be required, BQ job tracking will be required.

ADR4: DAG and model-level Data Lineage - for versioning of DAGs and dbt models it is recommended to use Git and dbt docs.
Rationale: it is recommended to leverage Git for versioning and standard functionality provided by dbt docs to avoid custom coding for dsata lineage.
Implication: it will require additional initial efforts to configure Git pipelines and dbt docs, if not done already.

ADR5: PII risk mitigation - high potential risk is visitorId if matched directly with geo.city and geo.region.
Rationale: store bare visitorId in raw data (bronze) layer without human accessibility, obfuscate (i.e. by hashing) visitorId by creating a surrogate unique transitively dependent key when moving data to staing (bronze) and mart (gold) layers. 
Implication: PII is protected by IAM in raw (bronze) layer. Only service accounts (automated processes) are allowed. Additional obfuscating of a visitorId will require a strong unified ruleset for possible future MDM issues handling - correct matching of a visitor with device fingerprints, analytics from other datasources etc. A possible solution could be a unified common table in BQ with all SKs of visitors, based on a durable component keys, from all data sources.

