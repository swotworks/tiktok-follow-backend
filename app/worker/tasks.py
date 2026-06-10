import asyncio
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import TaskLog, Task, User, WorkerAccount
from app.services.scraper import verify_follow_with_playwright

@celery_app.task(name="verify_tiktok_follow")
def verify_tiktok_follow(task_log_id: str, target_username: str, worker_username: str, proxy_url: str = None):
    """
    Celery task to verify if a worker followed the target user.
    """
    # Run the async playwright scraper in a sync celery task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    is_following = loop.run_until_complete(
        verify_follow_with_playwright(target_username, worker_username, proxy_url)
    )
    
    db = SessionLocal()
    try:
        task_log = db.query(TaskLog).filter(TaskLog.id == task_log_id).first()
        if not task_log:
            print(f"TaskLog {task_log_id} not found.")
            return
            
        if is_following:
            task_log.status = "Success"
            # Find task to get reward credits and update follow counts
            task = db.query(Task).filter(Task.id == task_log.task_id).first()
            if task:
                # Find the worker's user account to reward them
                worker_account = db.query(User).join(
                    WorkerAccount, WorkerAccount.user_id == User.id
                ).filter(
                    WorkerAccount.id == task_log.worker_id
                ).first()
                
                if worker_account:
                    worker_account.total_credits += task.reward_credits
                    
                task.current_follows += 1
                if task.current_follows >= task.target_follows:
                    task.status = "Completed"
                    
        else:
            task_log.status = "Failed"
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error in verify_tiktok_follow: {e}")
        # Mark as failed on DB error if possible
        try:
            if 'task_log' in locals() and task_log:
                task_log.status = "Failed"
                db.commit()
        except:
            pass
    finally:
        db.close()

from datetime import datetime, timedelta

@celery_app.task(name="check_unfollow_drops")
def check_unfollow_drops():
    """
    Cron job to check if workers have unfollowed targets after 24 hours.
    Processes in batches to avoid overwhelming the database.
    """
    db = SessionLocal()
    try:
        threshold_time = datetime.utcnow() - timedelta(hours=24)
        batch_size = 50
        offset = 0
        
        while True:
            # Fetch a batch of successful task logs older than 24 hours
            logs_batch = db.query(TaskLog).filter(
                TaskLog.status == "Success",
                TaskLog.created_at <= threshold_time
            ).offset(offset).limit(batch_size).all()
            
            if not logs_batch:
                break
                
            for task_log in logs_batch:
                # Find the task and worker account
                task = db.query(Task).filter(Task.id == task_log.task_id).first()
                worker_account = db.query(WorkerAccount).filter(WorkerAccount.id == task_log.worker_id).first()
                
                if not task or not worker_account:
                    continue
                    
                target_username = task.target_tiktok_username
                worker_username = worker_account.tiktok_username
                
                # Run the playwright scraper
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                is_following = loop.run_until_complete(
                    verify_follow_with_playwright(target_username, worker_username, None)
                )
                
                if is_following:
                    # Still following, mark as verified retained so we don't check again
                    task_log.status = "Verified_Retained"
                else:
                    # Unfollowed drop detected
                    task_log.status = "Dropped"
                    
                    # Deduct credits
                    user = db.query(User).filter(User.id == worker_account.user_id).first()
                    if user:
                        user.total_credits -= task.reward_credits
                        
                    # Add strike
                    worker_account.strikes += 1
                    if worker_account.strikes >= 3:
                        worker_account.is_active = False
            
            # Commit the batch
            db.commit()
            offset += batch_size
            
    except Exception as e:
        db.rollback()
        print(f"Error in check_unfollow_drops batch processing: {e}")
    finally:
        db.close()
