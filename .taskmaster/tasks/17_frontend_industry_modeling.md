# Task 17: 前端：行业建模页面

**状态:** pending | **优先级:** medium | **依赖:** 12, 13, 10

## 描述

实现行业建模流程页面，含模板选择和导入步骤。

## 详情

使用 Ant Design Steps 组件实现 ModelingStepper：

- **Step 1 选择模板**：TemplateCard 列表，显示模板名称、描述、标签、统计
- **Step 2 LLM 映射分析**：MVP 显示「即将推出」占位
- **Step 3 预览与调整**：展示将要导入的类型定义清单，用户可勾选/取消
- **Step 4 执行导入**：调用 `POST /templates/:id/apply`，成功后跳转到类型定义页

## 测试策略

选择模板 → 预览 → 导入 → 验证类型定义页出现新类型。
