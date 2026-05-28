# Content Structure Plan - AI设计师工作平台

## 1. Material Inventory

**Content Files:**
- `user_input_files/AI设计师工作网站设计概念.pdf` - 需求概念文档(PDF格式)
- `docs/ui_design_research/modern_ui_design_system.md` (~5000 words) - UI设计系统研究,涵盖色彩体系、组件模式、响应式策略
- `docs/ai_image_apis_analysis.md` (~4000 words) - AI图像API技术分析与集成架构

**Visual Assets:**
- `imgs/` - 待准备(logo、品牌图形)

**Data Files:**
- `data/brand_profile.json` - 品牌配置文件(需动态加载)

## 2. Website Structure

**Type:** SPA (单页应用)

**Reasoning:**
- 功能高度聚合:所有核心功能(品牌选择、需求填写、AI生成、结果展示)围绕单一工作流
- 实时交互:需要频繁的状态更新和API调用,SPA更适合处理
- 用户路径连贯:从选择品牌到生成结果是线性流程
- 目标用户(设计师)期望流畅的工具体验,非多页跳转

## 3. Section Breakdown

### Section 1: Header/Navigation
**Purpose**: 品牌标识、全局导航、用户状态

| 区域 | Component Pattern | 数据来源 | 内容提取 | Visual Asset |
|------|------------------|----------|----------|--------------|
| Logo | Nav Logo | 静态配置 | 品牌名称+图标 | `imgs/logo.svg` |
| 主导航 | Horizontal Nav | 静态 | 工作台/模板/历史/设置 | - |
| 用户状态 | User Menu | API | 用户头像+下拉菜单 | - |

### Section 2: 项目与品牌选择模块
**Purpose**: 快速切换项目和品牌上下文

| 区域 | Component Pattern | 数据来源 | 内容提取 | Visual Asset |
|------|------------------|----------|----------|--------------|
| 项目选择器 | Select Dropdown | API/本地 | 项目列表 | - |
| 品牌选择器 | Select Dropdown | `data/brand_profile.json` | 品牌名称列表 | - |
| 品牌信息预览 | Info Card | 动态加载 | 品牌色、字体、风格关键词 | 品牌Logo(动态) |

### Section 3: 生成需求填写模块
**Purpose**: 用户输入AI生成参数

| 区域 | Component Pattern | 数据来源 | 内容提取 | Visual Asset |
|------|------------------|----------|----------|--------------|
| 内容类型选择 | Radio Button Group | 静态配置 | 海报/Banner/社交媒体/产品图 | - |
| 主题关键词 | Tag Input | 用户输入 | 自定义标签 | - |
| 风格偏好 | Checkbox Group | 静态配置 | 极简/科技/商务/创意/潮流 | - |
| 构图比例 | Aspect Ratio Selector | 静态 | 1:1/16:9/9:16/4:3/自定义 | - |
| 详细描述 | Textarea | 用户输入 | 生成描述文本 | - |

### Section 4: AI平台选择与Prompt预览
**Purpose**: 选择AI服务并预览生成的Prompt

| 区域 | Component Pattern | 数据来源 | 内容提取 | Visual Asset |
|------|------------------|----------|----------|--------------|
| AI平台选择 | Tab Selector | 静态配置 | DALL-E 3/Midjourney/Stable Diffusion/通义万相 | 各平台Logo图标 |
| Prompt预览区 | Code Block | 动态生成 | 根据输入实时组装Prompt | - |
| Prompt编辑 | Editable Textarea | 用户可编辑 | 手动调整Prompt | - |
| 生成按钮 | Primary CTA | - | "开始生成" | - |

### Section 5: 生成结果展示与操作模块
**Purpose**: 展示AI生成结果,提供操作功能

| 区域 | Component Pattern | 数据来源 | 内容提取 | Visual Asset |
|------|------------------|----------|----------|--------------|
| 生成状态 | Progress Indicator | API实时 | 进度百分比/状态文字 | - |
| 结果网格 | Image Grid (2x2) | API返回 | 生成的图片(通常4张) | 动态生成图 |
| 单图操作 | Action Button Group | - | 放大/变体/下载/收藏 | - |
| 批量操作 | Toolbar | - | 全选/批量下载/删除 | - |
| 历史记录 | Side Panel/Drawer | API/本地 | 生成历史列表 | 缩略图 |

### Section 6: 模板系统与快速自定义
**Purpose**: 预设模板和快速参数配置

| 区域 | Component Pattern | 数据来源 | 内容提取 | Visual Asset |
|------|------------------|----------|----------|--------------|
| 模板分类 | Tab Navigation | 静态配置 | 电商/社媒/海报/品牌 | - |
| 模板卡片 | Template Card Grid | API/静态 | 模板名称+描述+预览 | 模板预览图 |
| 快速应用 | Quick Action Button | - | "使用此模板" | - |
| 参数预设 | Preset Pills | 静态/用户 | 常用参数组合 | - |

## 4. Content Analysis

**Information Density:** High (高密度)
- 多个交互表单和选择器
- 实时状态更新和API交互
- 图像展示和操作功能

**Content Balance:**
- Images: 动态(AI生成结果、模板预览)
- Data/Forms: 约60% (核心交互区域)
- Text: 约20% (标签、说明、状态)
- Content Type: **工具/表单驱动型**

**交互复杂度:** 高
- 多步骤工作流
- 实时Prompt生成预览
- 异步API调用和状态管理
- 拖拽、批量操作等高级交互
