from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.api import dependencies
from app.db.session import get_db

router = APIRouter()

@router.post("/add", response_model=schemas.WorkerAccount)
def add_worker(
    worker_in: schemas.WorkerAccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    existing_worker = db.query(models.WorkerAccount).filter(
        models.WorkerAccount.tiktok_username == worker_in.tiktok_username
    ).first()
    if existing_worker:
        raise HTTPException(
            status_code=400, detail="This TikTok username is already registered."
        )
    
    worker = models.WorkerAccount(
        user_id=current_user.id,
        tiktok_username=worker_in.tiktok_username,
        is_active=True
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker

@router.get("/", response_model=List[schemas.WorkerAccount])
def get_workers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    workers = db.query(models.WorkerAccount).filter(
        models.WorkerAccount.user_id == current_user.id
    ).all()
    return workers

@router.delete("/{worker_id}")
def delete_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    worker = db.query(models.WorkerAccount).filter(
        models.WorkerAccount.id == worker_id,
        models.WorkerAccount.user_id == current_user.id
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=404, detail="TikTok account not found or access denied."
        )
        
    db.delete(worker)
    db.commit()
    return {"message": "TikTok account successfully deleted"}

