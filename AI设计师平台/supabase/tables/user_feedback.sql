CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    generation_id UUID REFERENCES generation_history(id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL,
    feedback_content TEXT NOT NULL,
    rating INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);