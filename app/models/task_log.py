from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
from datetime import datetime

import uuid

class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("worker_accounts.id"), nullable=False, index=True)
    status = Column(String, default="Processing", nullable=False) # Processing, Success, Failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
