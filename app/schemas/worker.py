from pydantic import BaseModel
from uuid import UUID

class WorkerAccountBase(BaseModel):
    tiktok_username: str

class WorkerAccountCreate(WorkerAccountBase):
    pass

class WorkerAccountInDBBase(WorkerAccountBase):
    id: UUID
    user_id: UUID
    is_active: bool

    class Config:
        from_attributes = True

class WorkerAccount(WorkerAccountInDBBase):
    pass
