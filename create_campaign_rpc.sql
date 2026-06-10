-- CREATE CAMPAIGN SECURE TRANSACTION
-- Run this in your Supabase SQL Editor

CREATE OR REPLACE FUNCTION public.create_campaign_securely(
  p_target_username TEXT,
  p_target_follows INTEGER
)
RETURNS UUID AS $$
DECLARE
  v_cost INTEGER;
  v_user_credits INTEGER;
  v_task_id UUID;
BEGIN
  -- 1. Calculate cost (1 follow = 10 credits)
  v_cost := p_target_follows * 10;
  
  -- 2. Get user's current credits and lock the row for update
  SELECT total_credits INTO v_user_credits 
  FROM public.users 
  WHERE id = auth.uid()
  FOR UPDATE;
  
  -- 3. Check if they have enough credits
  IF v_user_credits < v_cost THEN
    RAISE EXCEPTION 'Not enough credits. You need % credits but only have %.', v_cost, v_user_credits;
  END IF;
  
  -- 4. Deduct the credits securely
  UPDATE public.users 
  SET total_credits = total_credits - v_cost 
  WHERE id = auth.uid();
  
  -- 5. Create the Campaign (Task)
  INSERT INTO public.tasks (creator_id, target_tiktok_username, reward_credits, target_follows, current_follows, status)
  VALUES (auth.uid(), p_target_username, 10, p_target_follows, 0, 'Active')
  RETURNING id INTO v_task_id;
  
  -- 6. Return the new task ID
  RETURN v_task_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
