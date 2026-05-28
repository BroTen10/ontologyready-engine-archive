CREATE TABLE user_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    brand_config JSONB NOT NULL,
    content_type TEXT NOT NULL,
    theme_keywords TEXT[],
    style_preferences TEXT[],
    aspect_ratio TEXT NOT NULL,
    special_requirements TEXT[],
    prompt_template TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);