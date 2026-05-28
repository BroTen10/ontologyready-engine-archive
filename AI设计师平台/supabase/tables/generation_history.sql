CREATE TABLE generation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES user_projects(id) ON DELETE CASCADE,
    ai_platform TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    generated_images TEXT[] NOT NULL,
    generation_params JSONB NOT NULL,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);