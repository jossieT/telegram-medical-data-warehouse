with stg_messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

dim_channels as (
    select * from {{ ref('dim_channels') }}
),

dim_dates as (
    select * from {{ ref('dim_dates') }}
),

final as (
    select
        m.message_id,
        c.channel_key,
        d.date_key,
        m.full_date as message_timestamp,
        m.message_text,
        m.message_length,
        m.view_count,
        m.forward_count,
        m.has_image
    from stg_messages m
    left join dim_channels c on m.channel_name = c.channel_name
    left join dim_dates d on m.date_pk = d.full_date
)

select * from final
