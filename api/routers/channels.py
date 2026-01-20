from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from .. import schemas

router = APIRouter(prefix="/api/channels", tags=["channels"])

@router.get("/{channel_name}/activity", response_model=schemas.ChannelActivity)
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    # Total posts
    count_query = text("""
        SELECT COUNT(*) 
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_key = c.channel_key
        WHERE c.channel_name = :name
    """)
    total_posts = db.execute(count_query, {"name": channel_name}).scalar()
    
    if not total_posts or total_posts == 0:
        raise HTTPException(status_code=404, detail="Channel not found or has no activity")

    # Daily trends
    daily_query = text("""
        SELECT d.full_date::text as date, COUNT(*) as post_count
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_key = c.channel_key
        JOIN dim_dates d ON m.date_key = d.date_key
        WHERE c.channel_name = :name
        GROUP BY d.full_date
        ORDER BY d.full_date DESC
        LIMIT 7
    """)
    daily_result = db.execute(daily_query, {"name": channel_name}).fetchall()
    daily_trends = [{"date": row[0], "post_count": row[1]} for row in daily_result]
    
    # Peak hours
    hour_query = text("""
        SELECT EXTRACT(HOUR FROM m.message_timestamp) as hour, COUNT(*) as post_count
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_key = c.channel_key
        WHERE c.channel_name = :name
        GROUP BY hour
        ORDER BY post_count DESC
        LIMIT 3
    """)
    hour_result = db.execute(hour_query, {"name": channel_name}).fetchall()
    peak_hours = [{"hour": int(row[0]), "post_count": row[1]} for row in hour_result]
    
    return {
        "channel_name": channel_name,
        "total_posts": total_posts,
        "daily_trends": daily_trends,
        "peak_hours": peak_hours
    }
