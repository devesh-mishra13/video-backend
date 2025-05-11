from pydantic import BaseModel
from typing import List, Optional

class CreateChatRequest(BaseModel):
    user_id: str  # the MongoDB ObjectId in string format
    chat_name: Optional[str] = "New Chat"

class FrameMetadata(BaseModel):
    frame_index: int
    timestamp: Optional[float] = None  # optional timestamp

class UploadFramesRequest(BaseModel):
    user_id: str
    chat_id: str
    frames: List[FrameMetadata]
