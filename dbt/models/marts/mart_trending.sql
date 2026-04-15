{{ config(materialized='table') }}

WITH latest_per_title AS (
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
        ROW_NUMBER() OVER (
            PARTITION BY tmdb_id, media_type
            ORDER BY polled_at DESC
        ) AS rn
    FROM {{ ref('stg_media_stream') }}
),

deduplicated AS (
    SELECT *
    FROM latest_per_title
    WHERE rn = 1
),

top_per_type AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY media_type
            ORDER BY rank ASC
        ) AS type_rank
    FROM deduplicated
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
FROM top_per_type
WHERE type_rank <= 10
ORDER BY media_type, rank ASC