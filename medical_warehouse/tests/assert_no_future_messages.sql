-- Messages cannot have a date in the future
select *
from {{ ref('stg_telegram_messages') }}
where full_date > current_timestamp
