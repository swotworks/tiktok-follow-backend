from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.models.base import Base

import uuid

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    target_tiktok_username = Column(String, nullable=False)
    reward_credits = Column(Integer, default=10, nullable=False)
    target_follows = Column(Integer, nullable=False)
    current_follows = Column(Integer, default=0, nullable=False)
    status = Column(String, default="Pending", nullable=False) # Pending, Active, Completed
    target_user_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
