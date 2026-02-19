{{ config(materialized='table') }}

SELECT DISTINCT
    GENERATE_UUID() AS traffic_sk,
    traffic_source,
    traffic_medium,
    traffic_keyword,
    referral_path
FROM {{ ref('stg_ga_sessions') }}