with detections as (
    select * from {{ ref('yolo_detections') }}
),

fct_messages as (
    select * from {{ ref('fct_messages') }}
),

final as (
    select
        d.message_id,
        m.channel_key,
        m.date_key,
        d.detected_object as detected_class,
        d.confidence_score,
        d.image_category
    from detections d
    left join fct_messages m on cast(d.message_id as text) = cast(m.message_id as text)
)

select * from final
