from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.api import dependencies
from app.db.session import get_db

router = APIRouter()

@router.post("/create", response_model=schemas.Task)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    total_cost = task_in.target_follows * 10
    if current_user.total_credits < total_cost:
        raise HTTPException(
            status_code=400, detail="Not enough credits to create this task."
        )
    
    # Deduct credits upfront
    current_user.total_credits -= total_cost
    
    task = models.Task(
        creator_id=current_user.id,
        target_tiktok_username=task_in.target_tiktok_username,
        reward_credits=10,
        target_follows=task_in.target_follows,
        current_follows=0,
        status="Active",
        target_user_ids=task_in.target_user_ids
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

from sqlalchemy import or_

@router.get("/pool", response_model=List[schemas.Task])
def get_task_pool(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    # Fetch tasks that are active, not created by the current user, and targeted to this user (or public)
    tasks = db.query(models.Task).filter(
        models.Task.status == "Active",
        models.Task.creator_id != current_user.id,
        or_(
            models.Task.target_user_ids.is_(None),
            models.Task.target_user_ids.contains([current_user.id])
        )
    ).all()
    return tasks

@router.post("/verify")
def verify_task(
    verify_in: schemas.TaskVerifyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    # Verify the task exists
    task = db.query(models.Task).filter(models.Task.id == verify_in.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Verify the worker belongs to current user
    worker = db.query(models.WorkerAccount).filter(
        models.WorkerAccount.id == verify_in.worker_id,
        models.WorkerAccount.user_id == current_user.id
    ).first()
    if not worker:
        raise HTTPException(status_code=403, detail="Worker account not found or access denied")
        
    # Check if a log already exists
    existing_log = db.query(models.TaskLog).filter(
        models.TaskLog.task_id == verify_in.task_id,
        models.TaskLog.worker_id == verify_in.worker_id
    ).first()
    if existing_log and existing_log.status in ["Success"]:
        raise HTTPException(status_code=400, detail="Task already completed for this account")
        
    # Create TaskLog as Success immediately
    task_log = models.TaskLog(
        task_id=task.id,
        worker_id=worker.id,
        status="Success"
    )
    db.add(task_log)
    
    # Reward worker's user
    current_user.total_credits += task.reward_credits
    
    # Update target follows
    task.current_follows += 1
    if task.current_follows >= task.target_follows:
        task.status = "Completed"
        
    db.commit()
    db.refresh(task_log)
    
    return {"task_log_id": task_log.id, "status": "Success"}

@router.get("/status/{task_log_id}")
def get_task_status(
    task_log_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    # Note: For strict security, we should ensure the log belongs to a worker owned by current_user
    task_log = db.query(models.TaskLog).filter(models.TaskLog.id == task_log_id).first()
    if not task_log:
        raise HTTPException(status_code=404, detail="Task Log not found")
    return {"task_log_id": task_log.id, "status": task_log.status}
