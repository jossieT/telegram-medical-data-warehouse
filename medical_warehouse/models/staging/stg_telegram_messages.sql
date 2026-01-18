with source as (
    select * from {{ source('raw', 'telegram_messages') }}
),

renamed as (
    select
        message_id,
        channel_name,
        message_date,
        message_text,
        views,
        forwards,
        has_media,
        image_path,
        raw_payload,
        loaded_at
    from source
),

final as (
    select
        -- IDs
        message_id,
        channel_name,
        
        -- Timestamps
        message_date as full_date,
        cast(message_date as date) as date_pk,
        
        -- Content
        message_text,
        length(message_text) as message_length,
        
        -- Metrics
        coalesce(views, 0) as view_count,
        coalesce(forwards, 0) as forward_count,
        
        -- Media
        has_media,
        case when has_media = true and image_path is not null then true else false end as has_image,
        image_path
        
    from renamed
    where message_date is not null
)

select * from final
