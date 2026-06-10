import os
import sys

# Add the current directory to sys.path to find 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from sqlalchemy import text

sql_commands = [
    # 1. Create notifications table
    """
    CREATE TABLE IF NOT EXISTS public.notifications (
      id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
      user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
      message TEXT NOT NULL,
      is_read BOOLEAN DEFAULT FALSE NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
    );
    """,
    
    # 2. Enable RLS
    "ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;",
    
    # 3. Drop existing select policy if exists, then create it
    "DROP POLICY IF EXISTS \"Users can see own notifications\" ON public.notifications;",
    """
    CREATE POLICY "Users can see own notifications" ON public.notifications
      FOR SELECT USING (auth.uid() = user_id);
    """,
    
    # 4. Add update policy for marking read
    "DROP POLICY IF EXISTS \"Users can update own notifications\" ON public.notifications;",
    """
    CREATE POLICY "Users can update own notifications" ON public.notifications
      FOR UPDATE USING (auth.uid() = user_id);
    """,
    
    # 5. Create/update reject_user_submission RPC function
    """
    CREATE OR REPLACE FUNCTION public.reject_user_submission(
      p_task_log_id UUID,
      p_reason TEXT DEFAULT 'Need Attention: You did not complete this task properly and submitted it anyway. Please follow again and submit it.'
    )
    RETURNS VOID AS $$
    DECLARE
      v_task_id UUID;
      v_worker_id UUID;
      v_user_id UUID;
      v_reward_credits INTEGER;
      v_status TEXT;
      v_is_admin BOOLEAN;
    BEGIN
      -- Verify caller is admin
      SELECT is_admin INTO v_is_admin FROM public.users WHERE id = auth.uid();
      IF v_is_admin IS NOT TRUE THEN
        RAISE EXCEPTION 'Unauthorized. Only admins can reject submissions.';
      END IF;

      -- Lock and retrieve details from task_log
      SELECT task_id, worker_id, status INTO v_task_id, v_worker_id, v_status
      FROM public.task_logs
      WHERE id = p_task_log_id
      FOR UPDATE;

      IF v_status != 'Success' THEN
        RAISE EXCEPTION 'Submission is not in Success state.';
      END IF;

      -- Get the user ID of the worker account
      SELECT user_id INTO v_user_id FROM public.worker_accounts WHERE id = v_worker_id;

      -- Get reward credits from the task
      SELECT reward_credits INTO v_reward_credits FROM public.tasks WHERE id = v_task_id;

      -- Deduct credits from the worker's user account (cap at 0 minimum)
      UPDATE public.users
      SET total_credits = GREATEST(0, total_credits - v_reward_credits)
      WHERE id = v_user_id;

      -- Decrement task current follows, set back to Active if it was Completed
      UPDATE public.tasks
      SET current_follows = GREATEST(0, current_follows - 1),
          status = 'Active'
      WHERE id = v_task_id;

      -- Delete the task log from the database completely
      DELETE FROM public.task_logs
      WHERE id = p_task_log_id;

      -- Insert inbox message (notification)
      INSERT INTO public.notifications (user_id, message)
      VALUES (v_user_id, p_reason);

    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
]

def main():
    print("Connecting to database and running notification/rejection migration...")
    with engine.connect() as conn:
        for i, sql in enumerate(sql_commands, 1):
            print(f"Executing statement {i}...")
            conn.execute(text(sql))
            conn.commit()
    print("Database migration and functions applied successfully!")

if __name__ == "__main__":
    main()
