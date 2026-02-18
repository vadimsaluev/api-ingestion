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

    Schema listing:

    visitId INT64,
    visitNumber INT64,
    visitStartTime INT64,
    date DATE,
    fullVisitorId STRING,
    channelGrouping STRING,

    device STRUCT<
        browser STRING,
        isMobile BOOL,
        operatingSystem STRING
    >,

    geoNetwork STRUCT<
        city STRING,
        cityId STRING,
        continent STRING,
        country STRING,
        latitude STRING,
        longitude STRING,
        metro STRING,
        networkDomain STRING,
        networkLocation STRING,
        region STRING,
        subContinent STRING
    >,

    totals STRUCT<
        bounces INT64,
        hits INT64,
        newVisits INT64,
        pageviews INT64,
        visits INT64
    >,

    trafficSource STRUCT<
        adContent STRING,
        keyword STRING,
        medium STRING,
        referralPath STRING,
        source STRING
    >,

    customDimensions ARRAY<STRUCT<
        index INT64,
        value STRING
    >>,

    hits_sample ARRAY<STRUCT<
        hitNumber INT64,
        hostname STRING,
        isInteraction BOOL,
        pagePath STRING,
        pageTitle STRING,
        time INT64,
        type STRING
    >>,

    -- metadata columns
    session_pk STRING
    load_timestamp TIMESTAMP,
    source_date DATE

    Implication: since this is a combination of a pure raw (files) and pre-processed (BQ bronze) layers - no analytical downstream (like Power BI, quick business data analytics) is allowed. We will create a modelled (gold, analytics-ready layer in the step with dbt).

ADR-2: Additional metadata - the minimal enchancement is:
    1. session_pk - determinated Primary Key for a session for a possible future parralelization/idempotency issue investigation/resolving. We will probably not use this in this case study.
    Important: to make this script production-ready, session_pk should be used for duplicates handling, but a duplicate resolving strategy will also be required: keeping duplicates vs overwriting duplicates.
    2. load_timestamp
    3. source_date
    4. source_gdrive_path

ADR-3: Suggested DQ checks at this stage:
    Rationale: since this layer is a bronze layer, no real data transformation is advised, however during moving the data towards conformed (silver/staging) and modelled (gold/mart) layers following Data Observability checks are advised:
    -- data observability
    DQ1. No NULLS in PK or its components:
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE session_pk IS NULL
    OR fullVisitorId IS NULL
    OR visitId IS NULL

    DQ2. No NULLs in visitStartTime:
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE visitStartTime IS NULL

    DQ3. Are there zeros in visits? Not a constraint but an indicator for possible division by zero in analytics.
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE totals.visits = 0

    -- data consistency
    DQ4. No negatives in metrics
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE totals.pageviews < 0
    OR totals.hits < 0

    DQ5. No duplicates of visitId within a single date:
    SELECT visitId, date, COUNT(1)
    FROM ga_sessions_raw
    GROUP BY visitId, date
    HAVING COUNT(1) > 1

    DQ6. Bounce consistency (1 bounce -> 1 pageview)
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE totals.bounces = 1
    AND totals.pageviews > 1

    DQ7. newVisits consistency (1 newVisits -> 1 visitNumber)
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE totals.newVisits = 1
    AND visitNumber > 1

    -- some business-critical checks
    DQ8. Channel must not be NULL, as it is critical for analytics
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE channelGrouping IS NULL

    DQ9. Geo must not be NULL, as it will not be possible to create splits by GEO with NULLs
    SELECT COUNT(1)
    FROM ga_sessions_raw
    WHERE geoNetwork.country IS NULL
    
    -- data completeness
    DQ10. Total records comparison after loading:
    if sum(records_fetched) != pagination.total_records:
        alert("Incomplete extraction")
    
    DQ11. Dates with empty records.
    SELECT date, COUNT(1)
    FROM ga_sessions_raw
    GROUP BY date
    HAVING COUNT(1) = 0

    -- data freshness (before starting the dbt transformation)
    SELECT MAX(load_timestamp)
    FROM ga_sessions_raw

    if NOW() - max(load_timestamp) < SLA_threshold -> we will throw an exception that there are gaps in time series or trigger missing data loading from closed periods.

    Implication: we will not physically touch the data in this layer, and it is recommended to leverage dbt for performing DQ checks on the way towards conformed (data observability) and modelled (business rules checks). An agreement what to do with the misses will be needed - skipping misses vs substituting missing data with suitable for analytics values (e.g. NULLs -> blanks etc.).
    Conceptually we separate technical observability checks from business semantic validation. Bronze (raw) ensures structural integrity, Silver (conformed/staging) ensures metric consistency, and Gold (mart) enforces analytics/KPI correctness.

Installation and running the script:
1. Clone the repository into the environment where you have Python of version >=3.10.0 installed.
2. Ensure you have credentials for Google Drive (gdrive path) and BQ connection (project, dataset, key).
3. Check requirements in the requirements.txt, ensure you have your dependencies satisfied
4. Run command from the terminal (configure desired start-date and end-date within script call command):
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