-- ADMIN RLS BYPASS POLICIES
-- Run this in your Supabase SQL Editor to allow admins to view all data!

-- 1. Allow Admins to SELECT all Users
CREATE POLICY "Admins can view all users" 
ON public.users 
FOR SELECT 
USING (
  (SELECT is_admin FROM public.users WHERE id = auth.uid()) = true
);

-- 2. Allow Admins to UPDATE all Users (for banning, adding credits)
CREATE POLICY "Admins can update all users" 
ON public.users 
FOR UPDATE 
USING (
  (SELECT is_admin FROM public.users WHERE id = auth.uid()) = true
);

-- 3. Allow Admins to SELECT all Worker Accounts
CREATE POLICY "Admins can view all worker accounts" 
ON public.worker_accounts 
FOR SELECT 
USING (
  (SELECT is_admin FROM public.users WHERE id = auth.uid()) = true
);

-- 4. Allow Admins to SELECT all Tasks
-- Note: 'Anyone can view active tasks' is already active, but this allows admins to see ALL tasks including completed/failed ones regardless of creator.
CREATE POLICY "Admins can view all tasks" 
ON public.tasks 
FOR SELECT 
USING (
  (SELECT is_admin FROM public.users WHERE id = auth.uid()) = true
);

-- 5. Allow Admins to SELECT all Task Logs
CREATE POLICY "Admins can view all task logs" 
ON public.task_logs 
FOR SELECT 
USING (
  (SELECT is_admin FROM public.users WHERE id = auth.uid()) = true
);
