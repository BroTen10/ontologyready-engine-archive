CREATE TABLE generation_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name TEXT NOT NULL,
    template_category TEXT NOT NULL,
    template_config JSONB NOT NULL,
    prompt_template TEXT NOT NULL,
    is_premium BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);