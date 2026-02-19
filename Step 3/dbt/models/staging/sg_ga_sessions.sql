{{ config(
    materialized='incremental',
    unique_key='session_pk'
) }}

WITH source_data AS (

    SELECT *
    FROM {{ source('bronze', 'ga_sessions_raw') }}

),

deduplicated AS (

    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY session_pk
            ORDER BY load_timestamp DESC
        ) AS rn
    FROM source_data

),

cleaned AS (

    SELECT
        session_pk,
        SAFE_CAST(visitId AS INT64) AS visit_id,
        SAFE_CAST(visitNumber AS INT64) AS visit_number,
        TIMESTAMP_SECONDS(SAFE_CAST(visitStartTime AS INT64)) AS visit_start_ts,
        DATE(date) AS session_date,
        fullVisitorId AS visitor_id,
        channelGrouping AS channel_grouping,

        device.browser AS browser,
        device.isMobile AS is_mobile,
        device.operatingSystem AS os,

        geoNetwork.city AS city,
        geoNetwork.country AS country,
        geoNetwork.continent AS continent,
        geoNetwork.region AS region,
        geoNetwork.subContinent AS sub_continent,

        totals.hits AS hits,
        totals.pageviews AS pageviews,
        totals.visits AS visits,
        totals.bounces AS bounces,
        totals.newVisits AS new_visits,

        trafficSource.source AS traffic_source,
        trafficSource.medium AS traffic_medium,
        trafficSource.keyword AS traffic_keyword,
        trafficSource.referralPath AS referral_path,

        load_timestamp,
        source_date,
        source_file_name,
        source_gdrive_path

    FROM deduplicated
    WHERE rn = 1
)

SELECT *
FROM cleaned

{% if is_incremental() %}
WHERE load_timestamp > (SELECT MAX(load_timestamp) FROM {{ this }})
{% endif %}