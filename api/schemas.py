from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# Reports
class TopProduct(BaseModel):
    product: str
    mention_count: int

class VisualContentStats(BaseModel):
    image_category: str
    count: int

class VisualContentResponse(BaseModel):
    category_distribution: List[VisualContentStats]
    channel_distribution: List[dict]
    comparison: dict

# Channels
class ChannelActivity(BaseModel):
    channel_name: str
    total_posts: int
    daily_trends: List[dict]
    peak_hours: List[dict]

# Search
class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_text: Optional[str]
    message_timestamp: datetime

    class Config:
        from_attributes = True
