# Task 4: API：统一错误响应规范

**状态:** pending | **优先级:** high | **依赖:** 2

## 描述

实现统一错误响应规范（RFC 9457），返回 JSON 格式 `{error: {code, message, details, request_id}}`。包含所有错误码。

## 详情

错误码：VALIDATION_ERROR(400), INVALID_JSON(400), UNAUTHORIZED(401), NOT_FOUND(404), CONFLICT(409), BUSINESS_RULE_ERROR(422), INTERNAL_ERROR(500)。每次请求生成唯一 request_id 并写入日志。details 字段为可选数组，用于字段级校验错误。

## 测试策略

触发各类错误场景，验证响应格式和状态码。
