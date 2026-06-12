-- PostgreSQL / Supabase Trigger for Manual Task Log Approvals
-- Run this in your Supabase SQL Editor.
-- This trigger automatically handles credits and task progress when you update a task log status to 'Success' directly in the database (e.g. from Supabase Studio).

CREATE OR REPLACE FUNCTION public.handle_task_log_approval()
RETURNS TRIGGER AS $$
DECLARE
  v_reward_credits INTEGER;
  v_target_follows INTEGER;
  v_current_follows INTEGER;
  v_worker_owner_id UUID;
BEGIN
  -- We only execute the reward logic if status is changing to 'Success'
  IF (NEW.status = 'Success' AND (TG_OP = 'INSERT' OR OLD.status IS DISTINCT FROM 'Success')) THEN
    
    -- 1. Get task details
    SELECT reward_credits, target_follows, current_follows
    INTO v_reward_credits, v_target_follows, v_current_follows
    FROM public.tasks
    WHERE id = NEW.task_id;
    
    IF NOT FOUND THEN
      RAISE WARNING 'Task not found for task_id %', NEW.task_id;
      RETURN NEW;
    END IF;

    -- 2. Find the owner of the worker account
    SELECT user_id INTO v_worker_owner_id
    FROM public.worker_accounts
    WHERE id = NEW.worker_id;

    IF NOT FOUND THEN
      RAISE WARNING 'Worker account not found for worker_id %', NEW.worker_id;
      RETURN NEW;
    END IF;

    -- 3. Reward the worker user with credits
    UPDATE public.users
    SET total_credits = total_credits + v_reward_credits
    WHERE id = v_worker_owner_id;

    -- 4. Update the task's follow counts and status
    v_current_follows := v_current_follows + 1;
    
    IF v_current_follows >= v_target_follows THEN
      UPDATE public.tasks
      SET current_follows = v_current_follows,
          status = 'Completed'
      WHERE id = NEW.task_id;
    ELSE
      UPDATE public.tasks
      SET current_follows = v_current_follows
      WHERE id = NEW.task_id;
    END IF;

  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if it exists
DROP TRIGGER IF EXISTS tr_verify_task_log ON public.task_logs;

-- Create trigger on task_logs table
CREATE TRIGGER tr_verify_task_log
  AFTER INSERT OR UPDATE OF status
  ON public.task_logs
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_task_log_approval();
