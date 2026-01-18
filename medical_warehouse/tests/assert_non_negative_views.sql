-- View count must be >= 0
select *
from {{ ref('stg_telegram_messages') }}
where view_count < 0
