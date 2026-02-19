{{ config(materialized='table') }}

SELECT DISTINCT
    GENERATE_UUID() AS device_sk,
    browser,
    os,
    is_mobile
FROM {{ ref('stg_ga_sessions') }}