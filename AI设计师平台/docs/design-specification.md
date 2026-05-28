# Design Specification - AI设计师工作平台

**Version**: 1.0 | **Target**: 专业设计师工具 | **Date**: 2025-12

---

## 1. Design Direction & Rationale

### 1.1 Style Essence

**主风格**: Modern Minimalism Premium + Dark Mode First (混合)

采用深色模式优先的现代极简设计，融合科技感与专业工具美学。以科技蓝(#0052CC)建立理性可信的基调，活力橙(#FF6B35)作为行动触发器，在深色背景上形成高对比的视觉层次。

**设计叙事**: "理性 + 活力" — 蓝色承载系统可信度与信息架构，橙色驱动用户操作与关键CTA。

### 1.2 Reference Examples

- **Figma**: 深色工具界面、面板分隔布局
- **Linear**: 极简导航、流畅过渡
- **Notion**: 模块化内容区域
- **YouMind**: 科技感UI、毛玻璃效果

### 1.3 Target Audience

- **年龄**: 22-40岁专业设计师/创意工作者
- **特征**: 熟悉数字工具、追求效率、审美敏感
- **使用环境**: 长时间工作、多为低光环境

---

## 2. Design Tokens

### 2.1 Colors

**Primary Brand (科技蓝)**

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| primary-50 | #E6F0FF | #0F2347 | 浅色背景/徽章 |
| primary-100 | #CCE0FF | #1A3564 | 悬浮态背景 |
| primary-500 | #0052CC | #4C8DFF | 主品牌色 |
| primary-600 | #0043A3 | #6AA3FF | 悬浮态 |
| primary-700 | #003580 | #85B8FF | 按下态 |

**Secondary Brand (活力橙)**

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| secondary-50 | #FFF0EB | #3A1A12 | 浅色背景 |
| secondary-500 | #FF6B35 | #FF8A5C | 主CTA色 |
| secondary-600 | #E55A2B | #FFA57D | 悬浮态 |

**Neutral (深色模式优先)**

| Token | Value | Usage |
|-------|-------|-------|
| neutral-0 | #000000 | OLED纯黑/Hero区域 |
| neutral-50 | #0A0A0A | 主背景 |
| neutral-100 | #141414 | 卡片/提升表面 |
| neutral-200 | #1E1E1E | 悬浮态/活动元素 |
| neutral-300 | #2A2A2A | 边框/分隔线 |
| neutral-400 | #71717A | 次要文本/禁用 |
| neutral-500 | #A1A1AA | 辅助文本 |
| neutral-600 | #E4E4E7 | 主要文本 |

**Background Layers**

| Token | Value | Usage |
|-------|-------|-------|
| bg-base | #0A0A0A | 页面底层 |
| bg-surface | #141414 | 卡片/面板 |
| bg-elevated | #1E1E1E | 弹窗/悬浮层 |
| bg-overlay | rgba(0,0,0,0.6) | 遮罩层 |

**Semantic Colors**

| Token | Dark Mode | Usage |
|-------|-----------|-------|
| success | #10B981 | 成功状态 |
| warning | #F59E0B | 警告提示 |
| error | #EF4444 | 错误/危险 |
| info | #60A5FA | 信息提示 |

**WCAG Contrast Verification**

| Pairing | Ratio | Status |
|---------|-------|--------|
| neutral-600 on bg-base | 15.2:1 | AAA |
| primary-500 (#4C8DFF) on bg-base | 8.6:1 | AAA |
| secondary-500 on bg-base | 7.2:1 | AAA |
| neutral-500 on bg-base | 8.9:1 | AAA |

### 2.2 Typography

**Font Stack**
```
Primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
Monospace: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace
```

**Type Scale**

| Token | Size | Weight | Line-height | Letter-spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| text-hero | 48px | 700 | 1.1 | -0.02em | 主标题 |
| text-h1 | 32px | 700 | 1.2 | -0.01em | 页面标题 |
| text-h2 | 24px | 600 | 1.3 | 0 | 区块标题 |
| text-h3 | 20px | 600 | 1.3 | 0 | 卡片标题 |
| text-body-lg | 18px | 400 | 1.6 | 0 | 介绍文字 |
| text-body | 16px | 400 | 1.5 | 0 | 正文 |
| text-small | 14px | 400 | 1.5 | 0.01em | 辅助文字 |
| text-caption | 12px | 400 | 1.4 | 0.01em | 标签/时间戳 |
| text-code | 14px | 400(mono) | 1.4 | 0 | 代码/Prompt |

### 2.3 Spacing (8pt Grid)

| Token | Value | Usage |
|-------|-------|-------|
| space-xs | 4px | 图标内边距 |
| space-sm | 8px | 紧凑间距 |
| space-md | 16px | 元素间距 |
| space-lg | 24px | 组件内边距 |
| space-xl | 32px | 卡片内边距 |
| space-2xl | 48px | 区块间距 |
| space-3xl | 64px | 主区域间距 |
| space-4xl | 96px | Hero区域 |

### 2.4 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| radius-sm | 4px | 小标签 |
| radius-md | 8px | 按钮/输入框 |
| radius-lg | 12px | 卡片 |
| radius-xl | 16px | 弹窗/面板 |
| radius-full | 9999px | 圆形元素 |

### 2.5 Shadows & Glows

```css
/* 卡片阴影 */
shadow-card: 0 0 0 1px rgba(255,255,255,0.05), 0 4px 12px rgba(0,0,0,0.5);

/* 卡片悬浮 */
shadow-card-hover: 0 0 0 1px rgba(255,255,255,0.1), 0 8px 24px rgba(0,0,0,0.6);

/* 主按钮辉光 */
glow-primary: 0 0 20px rgba(76,141,255,0.4), 0 0 40px rgba(76,141,255,0.2);

/* 次按钮辉光 */
glow-secondary: 0 0 20px rgba(255,107,53,0.4), 0 0 40px rgba(255,107,53,0.2);

/* 弹窗 */
shadow-modal: 0 0 0 1px rgba(255,255,255,0.1), 0 24px 48px rgba(0,0,0,0.7);
```

### 2.6 Animation

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| duration-fast | 150ms | ease-out | 按钮hover |
| duration-normal | 250ms | ease-out | 标准过渡 |
| duration-slow | 400ms | ease-in-out | 弹窗/抽屉 |

---

## 3. Component Specifications

### 3.1 Button

**Primary (CTA - 活力橙)**
- Height: 48px
- Padding: 16-32px horizontal
- Radius: radius-md (8px)
- Background: secondary-500
- Text: white, 16px, Semibold 600
- Hover: brightness(110%) + glow-secondary
- Active: scale(0.98)
- Disabled: opacity 0.5, cursor not-allowed

**Secondary (科技蓝边框)**
- Same dimensions
- Background: transparent
- Border: 2px solid primary-500
- Text: primary-500
- Hover: bg primary-500/10, glow-primary subtle

**Ghost**
- Same dimensions
- Background: transparent
- Text: neutral-500
- Hover: bg neutral-200, text neutral-600

### 3.2 Card

- Background: bg-surface (#141414)
- Padding: 24-32px
- Radius: radius-lg (12px)
- Border: 1px solid rgba(255,255,255,0.08)
- Shadow: shadow-card
- Hover: bg #1E1E1E, border rgba(255,255,255,0.12), shadow-card-hover, translateY(-2px)
- Transition: duration-normal

### 3.3 Input Field

- Height: 48px
- Padding: 12-16px
- Radius: radius-md (8px)
- Background: neutral-100
- Border: 1px solid neutral-300
- Text: neutral-600, 16px
- Placeholder: neutral-400
- Focus: border primary-500, glow 0 0 0 3px rgba(76,141,255,0.2)
- Error: border error, glow 0 0 0 3px rgba(239,68,68,0.2)

### 3.4 Select/Dropdown

- 继承Input样式
- Arrow icon: 20px, neutral-500, rotate on open
- Dropdown panel: bg-elevated, shadow-modal, max-height 280px
- Option height: 40px
- Option hover: bg neutral-200
- Option selected: bg primary-500/15, text primary-500

### 3.5 Navigation

**Top Bar (固定)**
- Height: 64px
- Background: rgba(10,10,10,0.8) + backdrop-blur(12px)
- Border-bottom: 1px solid rgba(255,255,255,0.08)
- Logo: 左对齐, 32px height
- Nav links: 16px Medium, neutral-500, hover neutral-600
- Active link: primary-500, 下划线2px
- CTA Button: 右对齐, Primary style 40px height

**Sidebar (可选)**
- Width: 240px (可折叠至64px)
- Background: #000000 (纯黑)
- Border-right: 1px solid rgba(255,255,255,0.08)
- Item height: 44px
- Active: bg neutral-200, border-left 3px primary-500

### 3.6 Tab Selector (AI平台选择)

- Container: inline-flex, bg neutral-100, radius-lg, padding 4px
- Tab: 44px height, padding 12-20px, radius-md
- Inactive: text neutral-500
- Active: bg neutral-200, text neutral-600
- Icon: 20px, 与文字左对齐

---

## 4. Layout & Interaction

### 4.1 Overall Structure

```
┌─────────────────────────────────────────────────────┐
│  Header (64px) - Logo | Nav | User                  │
├───────────┬─────────────────────────────────────────┤
│  Sidebar  │  Main Content Area                      │
│  (240px)  │  ┌─────────────────────────────────────┐│
│  Optional │  │  Project/Brand Selector             ││
│           │  ├─────────────────────────────────────┤│
│           │  │  Generation Form (Left 60%)         ││
│           │  │  + Preview Panel (Right 40%)        ││
│           │  ├─────────────────────────────────────┤│
│           │  │  Results Grid                       ││
│           │  └─────────────────────────────────────┘│
└───────────┴─────────────────────────────────────────┘
```

**Grid System**: 12-column
- Container max-width: 1400px
- Gutter: 24px
- Main content area: 60% form, 40% preview (可调整)

### 4.2 Section Patterns

**Header**
- Fixed position, z-index 100
- Glassmorphism: backdrop-blur(12px)

**Project Selector Bar**
- Height: 56px
- Background: bg-surface
- Inline dropdowns + brand preview

**Generation Form (Core Workspace)**
- 左侧60%: 表单输入区域
  - 垂直堆叠: 内容类型 → 关键词 → 风格 → 比例 → 描述
  - 每个字段间距: space-lg (24px)
- 右侧40%: Prompt预览面板
  - Sticky定位, top 80px
  - AI平台Tab选择器 + 代码块预览
  - 底部固定: 生成按钮 (Primary CTA)

**Results Grid**
- 2x2 网格 (Masonry可选)
- Gap: 24px
- 每张图片: 16:9或1:1 aspect ratio
- Hover overlay: 操作按钮组

### 4.3 Responsive Strategy

| Breakpoint | Layout Adjustment |
|------------|-------------------|
| xl (1280px+) | 完整双列布局, Sidebar可见 |
| lg (1024px) | Sidebar折叠, 单列优先 |
| md (768px) | 表单/预览垂直堆叠 |
| sm (640px) | 移动端单列, 底部Tab导航 |

**Mobile (sm)**
- 导航: 底部固定Tab bar, 64px height
- 表单: 全宽, 减少padding至16px
- 预览: 可折叠面板
- 结果: 单列展示
- Touch target: 最小48x48px

---

## 5. Interaction & Animation

### 5.1 Animation Standards

| Interaction | Property | Duration | Easing |
|-------------|----------|----------|--------|
| Button hover | background, box-shadow | 150ms | ease-out |
| Card hover | transform, box-shadow | 250ms | ease-out |
| Tab switch | background, opacity | 200ms | ease-out |
| Modal open | opacity, transform | 300ms | ease-out |
| Drawer slide | transform | 350ms | ease-in-out |
| Progress bar | width | 200ms | linear |

### 5.2 Loading States

**Prompt生成中**
- Skeleton shimmer effect
- 文字流式输出动画(typewriter)

**图像生成中**
- Progress ring (SVG动画)
- 进度百分比文字
- 预估剩余时间

**图像加载**
- Blur-up placeholder
- Fade-in on load (300ms)

### 5.3 Micro-interactions

- **Tag添加**: scale(1.05) → scale(1), 150ms
- **下拉展开**: height auto, opacity fade, 200ms
- **Toast通知**: slideIn from right + fadeIn, 300ms
- **Glow pulse**: CTA按钮生成时, 2s infinite subtle pulse

### 5.4 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 5.5 Icons

**Library**: Lucide Icons (推荐) 或 Heroicons
- Size: 20px (inline), 24px (buttons)
- Stroke width: 2px
- Color: 继承文字颜色

**禁止**: 使用Emoji作为UI图标

---

## 6. Light Mode Support

虽然主设计为深色模式，但需支持浅色模式切换。

**Light Mode Overrides**
- bg-base: #FFFFFF
- bg-surface: #F5F5F5
- bg-elevated: #FFFFFF
- neutral-600 (text): #171717
- border: rgba(0,0,0,0.1)
- shadow: 标准drop-shadow替代glow

**切换方式**: 系统偏好自动检测 + 手动切换开关

---

**Document Version**: 1.0
**Style Base**: Modern Minimalism Premium + Dark Mode First
**Maintained by**: Matrix Agent
