# AI设计师工作台 (AI Designer Platform)

一站式 AI 图像生成工作流平台。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 6
- **样式**: Tailwind CSS v3 + shadcn/ui + Radix UI
- **包管理**: npm
- **后端**: Supabase (认证、数据库、Edge Functions)
- **AI 图像**: DALL-E 3 / Pollinations.ai

## 项目结构

```
src/
├── components/          # UI 组件
│   ├── AuthModal.tsx       # 登录/注册弹窗
│   ├── ErrorBoundary.tsx   # 错误边界
│   ├── GenerationForm.tsx  # 生成需求表单
│   ├── Header.tsx          # 页面头部导航
│   ├── PromptPreview.tsx   # Prompt 预览/编辑器
│   ├── ProjectSelector.tsx # 项目选择器
│   ├── ResultsGrid.tsx     # 生成结果展示
│   └── TemplateLibrary.tsx # 模板库
├── contexts/
│   └── AuthContext.tsx     # 认证上下文
├── hooks/
│   ├── useBrandData.ts     # 品牌数据 Hook
│   └── use-mobile.tsx      # 移动端检测
├── lib/
│   ├── dataService.ts      # 数据服务 (Supabase CRUD + 图像生成)
│   ├── promptBuilder.ts    # Prompt 构建器
│   ├── supabase.ts         # Supabase 客户端 (含演示模式)
│   └── utils.ts            # 工具函数
├── types/
│   └── index.ts            # TypeScript 类型定义
├── App.tsx                 # 主应用组件
├── main.tsx                # 入口文件
└── index.css               # 全局样式
```

## 常用命令

```bash
npm run dev       # 启动开发服务器
npm run build     # TypeScript 编译 + Vite 构建
npm run build:prod  # 生产环境构建
npm run lint      # ESLint 检查
npm run preview   # 预览构建产物
npm run clean     # 清理 node_modules
```

## 环境变量

创建 `.env` 文件（参考 `.env.example`）:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_NAME=AI设计师工作台
VITE_API_ENDPOINT=/api
```

未配置 Supabase 时，应用自动进入演示模式（使用 Pollinations.ai 免费生成图像）。

## 演示模式

当 `.env` 文件未配置或缺失 Supabase 凭证时，应用自动进入演示模式：
- 使用 Mock Supabase 客户端（无数据库操作）
- 图像通过 Pollinations.ai 生成（免费，无需 API Key）
- 界面显示"演示模式"标签
