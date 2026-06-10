-- ADMIN APPROVAL WORKFLOW SQL SCRIPT
-- Run this in your Supabase SQL Editor

-- 1. OVERWRITE The Campaign Creation to default to 'Pending'
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
  v_cost := p_target_follows * 10;
  
  SELECT total_credits INTO v_user_credits 
  FROM public.users 
  WHERE id = auth.uid()
  FOR UPDATE;
  
  IF v_user_credits < v_cost THEN
    RAISE EXCEPTION 'Not enough credits. You need % credits but only have %.', v_cost, v_user_credits;
  END IF;
  
  UPDATE public.users 
  SET total_credits = total_credits - v_cost 
  WHERE id = auth.uid();
  
  -- CHANGED: Status is now 'Pending' instead of 'Active'
  INSERT INTO public.tasks (creator_id, target_tiktok_username, reward_credits, target_follows, current_follows, status)
  VALUES (auth.uid(), p_target_username, 10, p_target_follows, 0, 'Pending')
  RETURNING id INTO v_task_id;
  
  RETURN v_task_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 2. CREATE SECURE REJECT AND REFUND FUNCTION
CREATE OR REPLACE FUNCTION public.reject_campaign_securely(
  p_task_id UUID
)
RETURNS VOID AS $$
DECLARE
  v_creator_id UUID;
  v_target_follows INTEGER;
  v_refund_amount INTEGER;
  v_status TEXT;
  v_is_admin BOOLEAN;
BEGIN
  -- Verify the person calling this is an admin
  SELECT is_admin INTO v_is_admin FROM public.users WHERE id = auth.uid();
  IF v_is_admin IS NOT TRUE THEN
    RAISE EXCEPTION 'Unauthorized. Only admins can reject campaigns.';
  END IF;

  -- Lock the task and get details
  SELECT creator_id, target_follows, status INTO v_creator_id, v_target_follows, v_status
  FROM public.tasks
  WHERE id = p_task_id
  FOR UPDATE;

  IF v_status != 'Pending' THEN
    RAISE EXCEPTION 'Task is not in Pending state.';
  END IF;

  -- Calculate refund
  v_refund_amount := v_target_follows * 10;

  -- Update task status
  UPDATE public.tasks SET status = 'Rejected' WHERE id = p_task_id;

  -- Refund credits to the creator
  UPDATE public.users 
  SET total_credits = total_credits + v_refund_amount 
  WHERE id = v_creator_id;

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 3. CREATE SECURE APPROVE FUNCTION
CREATE OR REPLACE FUNCTION public.approve_campaign(
  p_task_id UUID
)
RETURNS VOID AS $$
DECLARE
  v_is_admin BOOLEAN;
BEGIN
  -- Verify the person calling this is an admin
  SELECT is_admin INTO v_is_admin FROM public.users WHERE id = auth.uid();
  IF v_is_admin IS NOT TRUE THEN
    RAISE EXCEPTION 'Unauthorized. Only admins can approve campaigns.';
  END IF;

  -- Update task status
  UPDATE public.tasks SET status = 'Active' WHERE id = p_task_id AND status = 'Pending';

END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
