with stg_messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channel_stats as (
    select
        channel_name,
        min(full_date) as first_post_date,
        max(full_date) as last_post_date,
        count(*) as total_posts,
        avg(view_count) as avg_views
    from stg_messages
    group by 1
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['channel_name']) }} as channel_key,
        channel_name,
        -- Simple logic for channel type mapping based on known channels
        case 
            when channel_name ilike '%pharma%' then 'Pharmaceutical'
            when channel_name ilike '%cosmetics%' then 'Cosmetics'
            when channel_name ilike '%medical%' or channel_name ilike '%med%' then 'Medical'
            else 'General'
        end as channel_type,
        first_post_date,
        last_post_date,
        total_posts,
        avg_views
    from channel_stats
)

select * from final
