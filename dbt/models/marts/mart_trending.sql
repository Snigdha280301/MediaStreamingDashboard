{{ config(materialized='table') }}

WITH latest_hour AS (
    SELECT DATE_TRUNC('hour', MAX(polled_at)) AS max_hour
    FROM {{ ref('stg_media_stream') }}
),

ranked AS (
    SELECT
        s.tmdb_id,
        s.title,
        s.media_type,
        s.rank,
        s.previous_rank,
        s.rank_change,
        s.popularity,
        s.vote_average,
        s.vote_count,
        s.original_language,
        s.endpoint_source,
        s.polled_at,
        ROW_NUMBER() OVER (
            PARTITION BY s.media_type, 
                         DATE_TRUNC('hour', s.polled_at)
            ORDER BY s.rank ASC
        ) AS poll_rank
    FROM {{ ref('stg_media_stream') }} s
    INNER JOIN latest_hour lh
        ON DATE_TRUNC('hour', s.polled_at) = lh.max_hour
)

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
    original_language,
    endpoint_source,
    polled_at,
    CASE
        WHEN rank_change > 0 THEN 'up'
        WHEN rank_change < 0 THEN 'down'
        ELSE 'stable'
    END AS rank_direction,
    CASE WHEN rank = 1 THEN true ELSE false END AS is_number_one,
    CASE WHEN previous_rank IS NULL 
         THEN true ELSE false END AS is_new_entry
FROM ranked
WHERE poll_rank <= 10
ORDER BY media_type, rank ASC