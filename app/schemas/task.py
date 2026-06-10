from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class TaskBase(BaseModel):
    target_tiktok_username: str
    reward_credits: int = 10
    target_user_ids: Optional[List[UUID]] = None

class TaskCreate(BaseModel):
    target_tiktok_username: str
    target_follows: int
    target_user_ids: Optional[List[UUID]] = None

class TaskInDBBase(TaskBase):
    id: UUID
    creator_id: UUID
    target_follows: int
    current_follows: int
    status: str

    class Config:
        from_attributes = True

class Task(TaskInDBBase):
    pass

class TaskVerifyRequest(BaseModel):
    task_id: UUID
    worker_id: UUID

class TaskLogBase(BaseModel):
    task_id: UUID
    worker_id: UUID
    status: str

class TaskLogCreate(TaskLogBase):
    pass

class TaskLogInDBBase(TaskLogBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TaskLog(TaskLogInDBBase):
    pass
