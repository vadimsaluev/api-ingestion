{{ config(materialized='incremental', unique_key='session_pk') }}

WITH base AS (

    SELECT *
    FROM {{ ref('stg_ga_sessions') }}

),

device_dim AS (
    SELECT * FROM {{ ref('dim_device') }}
),

geo_dim AS (
    SELECT * FROM {{ ref('dim_geo') }}
),

traffic_dim AS (
    SELECT * FROM {{ ref('dim_traffic_source') }}
)

SELECT
    b.session_pk,
    b.visit_id,
    b.visit_number,
    b.session_date,
    b.visit_start_ts,

    d.device_sk,
    g.geo_sk,
    t.traffic_sk,

    b.hits,
    b.pageviews,
    b.visits,
    b.bounces,
    b.new_visits

FROM base b
LEFT JOIN device_dim d
    ON b.browser = d.browser
    AND b.os = d.os
    AND b.is_mobile = d.is_mobile

LEFT JOIN geo_dim g
    ON b.country = g.country
    AND b.region = g.region
    AND b.city = g.city

LEFT JOIN traffic_dim t
    ON b.traffic_source = t.traffic_source
    AND b.traffic_medium = t.traffic_medium
    AND b.referral_path = t.referral_path

{% if is_incremental() %}
WHERE b.load_timestamp >
    (SELECT MAX(session_date) FROM {{ this }})
{% endif %}