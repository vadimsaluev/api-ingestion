{{ config(materialized='table') }}

WITH checks AS (

    SELECT
        CURRENT_TIMESTAMP() AS check_timestamp,
        'stg_ga_sessions' AS model_name,

        COUNT(*) AS total_rows,

        COUNTIF(session_pk IS NULL) AS null_session_pk,
        COUNTIF(visitor_id IS NULL) AS null_visitor_id,
        COUNTIF(hits IS NULL) AS null_hits,

        COUNTIF(visits = 0 AND pageviews > 0) AS invalid_visit_logic,

        COUNTIF(hits < pageviews) AS hits_less_than_pageviews

    FROM {{ ref('stg_ga_sessions') }}

)

SELECT
    *,
    CASE
        WHEN null_session_pk > 0 THEN 'FAIL'
        WHEN null_visitor_id > 0 THEN 'FAIL'
        WHEN invalid_visit_logic > 0 THEN 'FAIL'
        ELSE 'PASS'
    END AS overall_status
FROM checks