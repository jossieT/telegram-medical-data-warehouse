from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from ..database import get_db
from .. import schemas

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/messages", response_model=List[schemas.MessageSearchResult])
def search_messages(query: str, limit: int = 20, db: Session = Depends(get_db)):
    search_query = text("""
        SELECT 
            m.message_id, 
            c.channel_name, 
            m.message_text, 
            m.message_timestamp 
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_key = c.channel_key
        WHERE m.message_text ILIKE :q
        ORDER BY m.message_timestamp DESC
        LIMIT :limit
    """)
    result = db.execute(search_query, {"q": f"%{query}%", "limit": limit}).fetchall()
    
    return [
        {
            "message_id": row[0],
            "channel_name": row[1],
            "message_text": row[2],
            "message_timestamp": row[3]
        } for row in result
    ]
