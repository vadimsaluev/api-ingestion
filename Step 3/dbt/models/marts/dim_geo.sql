{{ config(materialized='table') }}

SELECT DISTINCT
    GENERATE_UUID() AS geo_sk,
    continent,
    country,
    region,
    city
FROM {{ ref('stg_ga_sessions') }}