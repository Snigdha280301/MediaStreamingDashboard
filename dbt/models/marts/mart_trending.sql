with ranked as (
    select
        tmdb_id,
        title,
        media_type,
        rank,
        popularity,
        polled_at,
        row_number() over (
            partition by date_trunc('hour', polled_at)
            order by rank asc
        ) as poll_rank
    from {{ ref('stg_media_stream') }}
)

select
    tmdb_id,
    title,
    media_type,
    rank,
    popularity,
    polled_at
from ranked
where poll_rank <= 10
