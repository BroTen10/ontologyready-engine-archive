# Task 3: API：API Key 认证中间件

**状态:** pending | **优先级:** high | **依赖:** 2

## 描述

实现 API Key 认证中间件，所有请求需携带 X-API-Key 请求头，无 Key 或错误返回 401。API Key 通过环境变量注入，首次启动未配置时自动生成 UUID。

## 详情

中间件拦截所有 `/api/v1/*` 请求。从环境变量 `API_KEY` 读取，未配置时生成 UUID 并打印到日志。错误响应格式遵循统一定义（UNAUTHORIZED 错误码）。控制台前端通过 `VITE_API_KEY` 注入。MVP 单一 Key，无用户概念。

## 测试策略

不带 Key 请求返回 401；错误 Key 返回 401；正确 Key 正常通过。
