# Task 12: 前端：项目框架搭建 + 全局配置

**状态:** pending | **优先级:** high | **依赖:** 无

## 描述

搭建前端项目：React 18 + Vite + TypeScript，集成所有核心依赖，实现全局 API Key 注入。

## 详情

技术栈：React 18 + Vite + TypeScript + Ant Design 5 + React Flow (xyflow) + React Router 6 + TanStack React Query + Axios + pnpm。

实现 ApiKeyProvider 组件：Axios 请求拦截器从环境变量 `VITE_API_KEY` 读取并注入 `X-API-Key` 请求头，响应拦截器统一处理 401。

配置 React Query 默认选项（staleTime, retry）。配置 Vite 代理（`/api` → `localhost:8000`）。

## 测试策略

启动前端项目，验证 Axios 请求自动携带 X-API-Key。
