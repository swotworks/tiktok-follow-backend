import os
import sys

# Add the current directory to sys.path to find 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from sqlalchemy import text

sql_commands = [
    # Create public.delete_user_securely RPC function
    """
    CREATE OR REPLACE FUNCTION public.delete_user_securely(
      p_user_id UUID
    )
    RETURNS VOID AS $$
    DECLARE
      v_is_admin BOOLEAN;
    BEGIN
      -- Verify caller is admin
      SELECT is_admin INTO v_is_admin FROM public.users WHERE id = auth.uid();
      IF v_is_admin IS NOT TRUE THEN
        RAISE EXCEPTION 'Unauthorized. Only admins can delete users.';
      END IF;

      -- Prevent admin from deleting themselves
      IF p_user_id = auth.uid() THEN
        RAISE EXCEPTION 'You cannot delete your own admin account.';
      END IF;

      -- Delete from auth.users (which cascades to public.users and worker accounts, tasks, logs, etc.)
      DELETE FROM auth.users WHERE id = p_user_id;

    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
]

def main():
    print("Connecting to database and applying delete_user_securely migration...")
    with engine.connect() as conn:
        for i, sql in enumerate(sql_commands, 1):
            print(f"Executing statement {i}...")
            conn.execute(text(sql))
            conn.commit()
    print("Database function delete_user_securely applied successfully!")

if __name__ == "__main__":
    main()
