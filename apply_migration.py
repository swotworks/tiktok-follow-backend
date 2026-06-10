import os
import sys

# Add the current directory to sys.path to find 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from sqlalchemy import text

sql_commands = [
    # 1. Add target_user_ids column to public.tasks
    "ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS target_user_ids UUID[] DEFAULT NULL;",
    
    # 2. Re-create create_campaign_securely RPC with 3 parameters
    """
    CREATE OR REPLACE FUNCTION public.create_campaign_securely(
      p_target_username TEXT,
      p_target_follows INTEGER,
      p_target_user_ids UUID[] DEFAULT NULL
    )
    RETURNS UUID AS $$
    DECLARE
      v_task_id UUID;
      v_is_admin BOOLEAN;
    BEGIN
      -- Verify the caller is an admin
      SELECT is_admin INTO v_is_admin FROM public.users WHERE id = auth.uid();
      IF v_is_admin IS NOT TRUE THEN
        RAISE EXCEPTION 'Unauthorized. Only admins can create campaigns.';
      END IF;

      -- Admins bypass credit deduction & verification.
      -- Insert campaign directly as 'Active' with the targeting user array.
      INSERT INTO public.tasks (
        creator_id, 
        target_tiktok_username, 
        reward_credits, 
        target_follows, 
        current_follows, 
        status, 
        target_user_ids
      )
      VALUES (
        auth.uid(), 
        p_target_username, 
        10, 
        p_target_follows, 
        0, 
        'Active', 
        p_target_user_ids
      )
      RETURNING id INTO v_task_id;
      
      RETURN v_task_id;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
]

def main():
    print("Connecting to database and running migration...")
    with engine.connect() as conn:
        for i, sql in enumerate(sql_commands, 1):
            print(f"Executing statement {i}...")
            conn.execute(text(sql))
            conn.commit()
    print("Database migration and function definition applied successfully!")

if __name__ == "__main__":
    main()
