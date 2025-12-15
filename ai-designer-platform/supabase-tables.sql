-- 确保uuid-ossp扩展已安装
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 先删除现有表（如果存在），使用CASCADE选项处理依赖关系
DROP TABLE IF EXISTS generation_templates CASCADE;
DROP TABLE IF EXISTS generation_history CASCADE;
DROP TABLE IF EXISTS user_templates CASCADE;

-- 创建用户模板表
CREATE TABLE user_templates (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  content_type TEXT NOT NULL,
  style_preferences TEXT[] DEFAULT '{}',
  keywords TEXT[] DEFAULT '{}',
  aspect_ratio TEXT NOT NULL,
  special_requirements TEXT[] DEFAULT '{}',
  prompt_template TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建生成历史表
CREATE TABLE generation_history (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id TEXT,
  project_id TEXT,
  content_type TEXT NOT NULL,
  keywords TEXT[] DEFAULT '{}',
  style_preferences TEXT[] DEFAULT '{}',
  aspect_ratio TEXT NOT NULL,
  special_requirements TEXT[] DEFAULT '{}',
  ai_platform TEXT NOT NULL,
  prompt TEXT NOT NULL,
  result_images TEXT[] DEFAULT '{}',
  status TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建生成模板表
CREATE TABLE generation_templates (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  category TEXT,
  content_type TEXT NOT NULL,
  style_preferences TEXT[] DEFAULT '{}',
  keywords TEXT[] DEFAULT '{}',
  aspect_ratio TEXT NOT NULL,
  special_requirements TEXT[] DEFAULT '{}',
  prompt_template TEXT NOT NULL,
  is_preset BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加索引
CREATE INDEX idx_user_templates_user_id ON user_templates(user_id);
CREATE INDEX idx_generation_history_user_id ON generation_history(user_id);
CREATE INDEX idx_generation_templates_is_preset ON generation_templates(is_preset);

-- 添加RLS策略（如果需要，可以取消注释）
-- ALTER TABLE user_templates ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "User can only access own templates" ON user_templates
--   FOR ALL USING (user_id = auth.uid());

-- ALTER TABLE generation_history ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "User can only access own generation history" ON generation_history
--   FOR ALL USING (user_id = auth.uid());

-- ALTER TABLE generation_templates ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Anyone can read preset templates" ON generation_templates
--   FOR SELECT USING (is_preset = true);