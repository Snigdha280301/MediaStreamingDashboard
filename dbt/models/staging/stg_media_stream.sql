with source as (
    select * from {{ source('raw', 'media_stream') }}
),

renamed as (
    select
        cast(tmdb_id    as bigint)    as tmdb_id,
        cast(title      as string)    as title,
        cast(media_type as string)    as media_type,
        cast(rank       as int)       as rank,
        cast(popularity as double)    as popularity,
        cast(polled_at as timestamp) as polled_at
    from source
    where tmdb_id is not null
      and title   is not null
)

select * from renamed
