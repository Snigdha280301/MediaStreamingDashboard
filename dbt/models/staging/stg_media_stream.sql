{{ config(materialized='view') }}

SELECT
    tmdb_id,
    title,
    media_type,
    rank,
    previous_rank,
    rank_change,
    popularity,
    vote_average,
    vote_count,
    genre_ids,
    overview,
    release_date,
    original_language,
    endpoint_source,
    CAST(polled_at AS TIMESTAMP) AS polled_at,
    DATE(polled_at) AS poll_date,
    HOUR(polled_at) AS poll_hour
FROM {{ source('raw', 'media_stream') }}
WHERE title IS NOT NULL
  AND tmdb_id IS NOT NULL