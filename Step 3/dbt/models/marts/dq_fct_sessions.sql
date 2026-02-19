{{ config(materialized='table') }}

SELECT
    CURRENT_TIMESTAMP() AS check_timestamp,
    COUNT(*) AS total_rows,

    COUNTIF(pageviews < hits) AS pageviews_less_than_hits,
    COUNTIF(bounces > visits) AS invalid_bounce_logic,

    CASE
        WHEN COUNTIF(pageviews < hits) > 0 THEN 'FAIL'
        WHEN COUNTIF(bounces > visits) > 0 THEN 'FAIL'
        ELSE 'PASS'
    END AS overall_status

FROM {{ ref('fct_sessions') }}