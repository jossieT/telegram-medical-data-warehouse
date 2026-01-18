with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2020-01-01' as date)",
        end_date="cast('2030-01-01' as date)"
    ) }}
),

final as (
    select
        date_day as full_date,
        cast(to_char(date_day, 'YYYYMMDD') as integer) as date_key,
        to_char(date_day, 'Day') as day_name,
        extract(isodow from date_day) as day_of_week,
        extract(week from date_day) as week_of_year,
        extract(month from date_day) as month,
        to_char(date_day, 'Month') as month_name,
        extract(quarter from date_day) as quarter,
        extract(year from date_day) as year,
        case when extract(isodow from date_day) in (6, 7) then true else false end as is_weekend
    from date_spine
)

select * from final
