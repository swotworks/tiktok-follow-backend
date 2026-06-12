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
    
    if existing_log:
        if existing_log.status == "Success":
            raise HTTPException(status_code=400, detail="Task already completed for this account")
        elif existing_log.status == "Pending":
            raise HTTPException(status_code=400, detail="Verification request is already pending review")
        
        # If it was "Failed" (or anything else), update it to "Pending"
        existing_log.status = "Pending"
        db.commit()
        db.refresh(existing_log)
        return {"task_log_id": existing_log.id, "status": "Pending"}
        
    # Create TaskLog as Pending
    task_log = models.TaskLog(
        task_id=task.id,
        worker_id=worker.id,
        status="Pending"
    )
    db.add(task_log)
    db.commit()
    db.refresh(task_log)
    
    return {"task_log_id": task_log.id, "status": "Pending"}

@router.post("/admin/approve/{task_log_id}")
def approve_task_log(
    task_log_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can approve tasks")
        
    task_log = db.query(models.TaskLog).filter(models.TaskLog.id == task_log_id).first()
    if not task_log:
        raise HTTPException(status_code=404, detail="Task Log not found")
        
    if task_log.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve task log with status: {task_log.status}")
        
    # Get task to reward credits and update follow counts
    task = db.query(models.Task).filter(models.Task.id == task_log.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Associated task not found")
        
    # Get the worker's user account to reward them
    worker_account = db.query(models.WorkerAccount).filter(
        models.WorkerAccount.id == task_log.worker_id
    ).first()
    if not worker_account:
        raise HTTPException(status_code=404, detail="Worker account not found")
        
    worker_user = db.query(models.User).filter(models.User.id == worker_account.user_id).first()
    if not worker_user:
        raise HTTPException(status_code=404, detail="Worker's user account not found")
        
    # Reward credits
    worker_user.total_credits += task.reward_credits
    
    # Increment task progress
    task.current_follows += 1
    if task.current_follows >= task.target_follows:
        task.status = "Completed"
        
    # Update log status
    task_log.status = "Success"
    
    db.commit()
    return {"task_log_id": task_log.id, "status": "Success"}

@router.post("/admin/reject/{task_log_id}")
def reject_task_log(
    task_log_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can reject tasks")
        
    task_log = db.query(models.TaskLog).filter(models.TaskLog.id == task_log_id).first()
    if not task_log:
        raise HTTPException(status_code=404, detail="Task Log not found")
        
    if task_log.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Cannot reject task log with status: {task_log.status}")
        
    # Update status to Failed
    task_log.status = "Failed"
    db.commit()
    return {"task_log_id": task_log.id, "status": "Failed"}

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
