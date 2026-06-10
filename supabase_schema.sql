-- SUPABASE MIGRATION SCHEMA & RLS POLICIES
-- Run this entire script in your Supabase SQL Editor

-- 1. Create Tables
CREATE TABLE public.users (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  total_credits INTEGER DEFAULT 0 NOT NULL,
  is_admin BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE public.worker_accounts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  tiktok_username TEXT UNIQUE NOT NULL,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  strikes INTEGER DEFAULT 0 NOT NULL
);

CREATE TABLE public.tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  creator_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
  target_tiktok_username TEXT NOT NULL,
  reward_credits INTEGER DEFAULT 10 NOT NULL,
  target_follows INTEGER NOT NULL,
  current_follows INTEGER DEFAULT 0 NOT NULL,
  status TEXT DEFAULT 'Active' NOT NULL
);

CREATE TABLE public.task_logs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  task_id UUID REFERENCES public.tasks(id) ON DELETE CASCADE NOT NULL,
  worker_id UUID REFERENCES public.worker_accounts(id) ON DELETE CASCADE NOT NULL,
  status TEXT DEFAULT 'Processing' NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.worker_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_logs ENABLE ROW LEVEL SECURITY;

-- 3. Create RLS Policies

-- USERS: Can only read and update their own row
CREATE POLICY "Users can read own data" ON public.users
  FOR SELECT USING (auth.uid() = id);

-- WORKER ACCOUNTS: Can only CRUD their own accounts
CREATE POLICY "Workers are isolated to owner" ON public.worker_accounts
  FOR ALL USING (auth.uid() = user_id);

-- TASKS: 
-- Anyone can see Active tasks (Task Pool)
CREATE POLICY "Anyone can view active tasks" ON public.tasks
  FOR SELECT USING (status = 'Active');
-- Creators can manage their own tasks
CREATE POLICY "Creators manage own tasks" ON public.tasks
  FOR ALL USING (auth.uid() = creator_id);

-- TASK LOGS: 
-- Workers can see their own logs
CREATE POLICY "Workers can see their logs" ON public.task_logs
  FOR SELECT USING (
    worker_id IN (SELECT id FROM public.worker_accounts WHERE user_id = auth.uid())
  );
-- Workers can insert logs for their accounts
CREATE POLICY "Workers can create logs" ON public.task_logs
  FOR INSERT WITH CHECK (
    worker_id IN (SELECT id FROM public.worker_accounts WHERE user_id = auth.uid())
  );

-- 4. Supabase Auth Trigger (Auto-create user row on signup)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, username, email)
  VALUES (
    new.id, 
    new.raw_user_meta_data->>'username', 
    new.email
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();
