from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from ..database import get_db
from .. import schemas

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/top-products", response_model=List[schemas.TopProduct])
def get_top_products(limit: int = 10, db: Session = Depends(get_db)):
    # Simple keyword extraction/count from messages for demonstration
    # In a real scenario, this would query a pre-computed dbt table
    query = text("""
        SELECT word as product, count(*) as mention_count
        FROM (
            SELECT unnest(string_to_array(lower(message_text), ' ')) as word
            FROM fct_messages
            WHERE message_text IS NOT NULL
        ) words
        WHERE word IN ('paracetamol', 'amoxicillin', 'ibuprofen', 'insulin', 'vitamin', 'mask', 'alcohol')
        GROUP BY word
        ORDER BY mention_count DESC
        LIMIT :limit
    """)
    result = db.execute(query, {"limit": limit})
    return [{"product": row[0], "mention_count": row[1]} for row in result]

@router.get("/visual-content", response_model=schemas.VisualContentResponse)
def get_visual_stats(db: Session = Depends(get_db)):
    # Category Distribution
    cat_query = text("SELECT image_category, COUNT(*) FROM fct_image_detections GROUP BY image_category")
    cat_result = db.execute(cat_query).fetchall()
    category_distribution = [{"image_category": row[0], "count": row[1]} for row in cat_result]
    
    # Channel Distribution
    chan_query = text("""
        SELECT c.channel_name, COUNT(*) as detections 
        FROM fct_image_detections d
        JOIN dim_channels c ON d.channel_key = c.channel_key
        GROUP BY c.channel_name
    """)
    chan_result = db.execute(chan_query).fetchall()
    channel_distribution = [{"channel_name": row[0], "detections": row[1]} for row in chan_result]
    
    # Comparison
    comp_query = text("""
        SELECT 
            image_category, 
            AVG(m.view_count) as avg_views 
        FROM fct_image_detections d
        JOIN fct_messages m ON cast(d.message_id as text) = cast(m.message_id as text)
        GROUP BY image_category
    """)
    comp_result = db.execute(comp_query).fetchall()
    comparison = {row[0]: float(row[1]) for row in comp_result}
    
    return {
        "category_distribution": category_distribution,
        "channel_distribution": channel_distribution,
        "comparison": comparison
    }
