-- RUN THIS IN SUPABASE SQL EDITOR
-- This fixes the issue where users cannot read or create their own profiles due to strict RLS security.

-- 1. Allow users to insert their own profile when they register
CREATE POLICY "Users can insert their own profile" 
ON public.users 
FOR INSERT 
WITH CHECK (auth.uid() = id);

-- 2. Allow users to view their own profile (Needed for AuthContext to load)
CREATE POLICY "Users can view their own profile" 
ON public.users 
FOR SELECT 
USING (auth.uid() = id);

-- 3. Allow users to update their own profile (Optional but good practice)
CREATE POLICY "Users can update their own profile" 
ON public.users 
FOR UPDATE 
USING (auth.uid() = id);
