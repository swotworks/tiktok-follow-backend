import os
import sys

# Add the current directory to sys.path to find 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine
from sqlalchemy import text

sql_commands = [
    # Drop existing policy if any, then create the DELETE policy
    "DROP POLICY IF EXISTS \"Users can delete own notifications\" ON public.notifications;",
    """
    CREATE POLICY "Users can delete own notifications" ON public.notifications
      FOR DELETE USING (auth.uid() = user_id);
    """
]

def main():
    print("Connecting to database and applying notification delete RLS policy...")
    with engine.connect() as conn:
        for i, sql in enumerate(sql_commands, 1):
            print(f"Executing statement {i}...")
            conn.execute(text(sql))
            conn.commit()
    print("Notification delete policy applied successfully!")

if __name__ == "__main__":
    main()
