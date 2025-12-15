# Supabase 在 AI 应用开发中的最佳实践蓝图

面向全栈与后端工程师、架构师、AI 应用开发者与技术负责人,本文给出一套以 Supabase 为核心的 AI 应用工程化蓝图,围绕认证与授权、文件存储与 CDN 策略、数据库与检索设计、Edge Functions 调用第三方 AI API、Realtime 状态管理,以及性能与安全优化展开,形成从设计到落地、从上线到演进的完整方法论与操作清单。文中的方案与建议,均以 Supabase 官方能力为底座,并辅以业内可信资料与示例,以确保可落地、可扩展、可维护。[^1][^2]

---

## 引言与总体架构:为何以 Supabase 为 AI 应用开发平台

生成式 AI 正在重塑应用形态,但任何智能体验的背后,依然是身份、数据、存储、函数、实时与安全等通用工程问题的系统性协同。Supabase 以 PostgreSQL 为核心,提供 Auth(认证与授权)、Storage(文件存储)、Edge Functions(边缘函数)、Realtime(实时)、Database(数据库与扩展)等模块化能力,开箱即用且彼此协同,能够以最少的胶水代码将 AI 能力安全、稳定地集成到现代应用之中。[^1][^2][^4][^5]

在总体架构上,建议的蓝图包含以下关键链路:前端通过 Auth 完成登录与会话维护;用户上传的媒体与提示词上下文经由受控后端路径写入 Storage;AI 侧的任务由 Edge Functions 以受保护的方式调用第三方模型 API;向量检索与语义搜索在 PostgreSQL 中以 pgvector 扩展承载;聊天与任务进度通过 Realtime 进行低延迟广播与 Presence 状态同步;全程以行级安全(Row Level Security,RLS)为数据访问边界,辅以最小权限策略与端到端可观测性。[^2][^5][^6][^12][^13][^20][^21][^22]

为便于把握职责边界,下表给出 Supabase 核心能力与 AI 应用职责的映射,作为后续章节的导航。

表 1:Supabase 核心能力与 AI 应用职责映射

| 模块 | 在 AI 应用中的职责 | 关键机制与要点 |
|---|---|---|
| Auth | 身份认证、会话与授权边界 | JWT、MFA、OAuth/SSO;与 RLS 联合实现最小权限[^6] |
| Storage | 用户上传与 AI 产物的存储与分发 | 受控上传、对象可见性与访问策略;路径命名规范[^5] |
| Edge Functions | 第三方 AI 模型调用的安全代理 | 密钥隔离、幂等重试、限流与审计;CORS 管控[^16][^17][^18] |
| Realtime | 任务进度广播与在线状态(Presence) | 频道模型、事件压缩、断线重连与一致性保障[^20][^21][^22] |
| Database | 数据结构、检索与扩展 | pgvector、pg_graphql、pg_net;索引与分区[^8][^9][^10][^11] |

这张蓝图的核心价值在于,将 AI 应用的“能力层”(模型与推理)与“工程层”(认证、存储、数据、实时、安全)清晰解耦,同时以 RLS 为统一安全边界贯穿数据访问,以获得稳定、可演进、可观测的端到端系统。

### Supabase 模块协同与边界

模块协同的关键,是身份、函数与存储在 RLS 下的一致性边界。

首先,Auth 提供 JWT 与用户标识,RLS 基于这些claims表达策略,形成数据访问的“可见性”与“可改性”。其次,Edge Functions 在处理第三方 AI 交互时,承担“受控代理”的角色:在函数侧读取环境变量中的受保护密钥,完成鉴权、参数构造与幂等处理;对于需要写入的数据库对象与 Storage 对象,RLS 仍然以调用方(常见为 anon 角色)的身份执行授权检查。再次,Storage 承担对象存储与分发职责,应遵循受控上传、最小公开与路径规范(详见后文)。[^2][^6][^7]

Edge Functions 的常见误区是“函数内部使用 service_role 就意味着绕过 RLS”。实务中,即使函数内部以 service_role 访问,RLS 仍可能基于调用者角色评估策略;因此正确的做法是同时授权 anon 与 service_role 两类角色,或显式地以调用者身份评估策略,从而避免“new row violates row-level security policy”错误(详见 RLS 章节)。[^7]

---

## 认证与授权:邮箱登录、社交登录与安全策略

Supabase Auth 提供密码、魔法链接、一次性密码(OTP)、社交登录(OAuth)、单点登录(SSO)与多因素认证(MFA)等多种方式,并以 JWT 作为会话基础,与 RLS 配合实现数据访问的最小权限。前端侧建议以“初始化加载 + 轻量监听”的方式管理会话:页面加载时调用 getUser 做一次性身份确认,onAuthStateChange 回调仅做同步状态更新,避免在回调中执行任何异步操作,以免导致死锁或 UI 卡顿。[^6]

表 2:认证方法对比与适用场景

| 方法 | 典型场景 | 优点 | 注意事项 |
|---|---|---|---|
| 密码登录 | 传统账号体系 | 简单直观 | 强制强度与过期策略,搭配 MFA 提升安全性[^6] |
| 魔法链接 | 低摩擦登录 | 免记密码 | 邮件安全与链接有效期控制[^6] |
| OTP(短信/邮件) | 快速验证 | 高便利性 | 供应商计费与可达性管理[^6] |
| 社交登录(OAuth) | 主流平台用户 | 转化率高 | 回调域校验,用户资料映射与隐私合规[^6] |
| SSO(企业) | 企业统一身份 | 安全合规 | 与企业 IdP 集成、审计与策略细化[^6] |
| MFA(短信/邮箱/基于 App) | 安全敏感操作 | 风险显著降低 | 备份验证码与恢复流程[^6] |

授权方面,RLS 将“身份”映射为“访问控制策略”,以“auth.uid()”与角色(auth.role())等claims表达访问边界。最佳实践是将“能否访问”与“访问后能做什么”拆解为 SELECT/INSERT/UPDATE/DELETE 四类操作策略,并以数据归属为基本单元进行定义(例如仅本人或所属团队可读写)。[^7]

### 前端会话与状态管理

前端会话管理建议采用以下范式:

- 初始化:在应用挂载后一次性调用 getUser 获取当前用户,设置 loading 状态,避免不必要的加载抖动。
- 监听:使用 onAuthStateChange 仅同步本地用户态(例如 setUser(session?.user || null)),不在回调中执行异步请求或复杂逻辑。
- 登录/登出:封装 signInWithPassword 与 signOut 方法,统一在业务层处理错误与提示。
- 路由守卫:所有需要鉴权的页面与 API 请求,均以 getUser 的结果或状态容器的 user 是否存在作为守卫条件。

该模式可显著降低状态不一致与 UI 卡死的风险,同时保证登录/登出语义的一致性。[^6]

### RLS 授权策略设计

RLS 的核心在于以清晰的规则表达“谁能在何种条件下访问什么数据”。要点如下:

- 使用 auth.uid() 绑定数据归属,实现“本人/本团队可读写、他人不可见”的默认语义。
- 将策略按操作拆分(SELECT/INSERT/UPDATE/DELETE),避免用 FOR ALL 涵盖所有操作而误伤读取路径。
- 在涉及 Edge Functions 写入的场景,显式允许 anon 与 service_role 两类角色,以避免因调用身份导致的策略拒绝。
- 定期使用性能分析工具与执行计划(explain/analyze)检查策略开销,确保高基数数据下的可扩展性。[^7][^25]

---

## 文件存储与 CDN 配置:安全上传、访问控制与路径命名

在 AI 应用中,文件存储承担两类职责:一是承载用户上传的提示词上下文(如文档、图片、音频),二是保存模型生成的结果(如合成图像、标注文件、摘要)。Supabase Storage 提供受控上传、桶级策略与公开访问能力,建议遵循“最小暴露面”的默认策略:非必要不设公开,采用签名 URL 或基于策略的受限访问;如确需公开,请以“可控可撤销”为前提(例如仅公开特定前缀或生命周期有限的链接)。[^5][^24]

表 3:典型文件类型与存储策略建议

| 文件类型 | 桶与可见性 | 访问策略 | 说明 |
|---|---|---|---|
| 用户上传图片/音频/文档 | 私有桶(如 user-content) | 签名 URL 或 RLS 授权 | 默认私有,按需限权访问[^5] |
| AI 生成图片/视频 | 私有桶(如 ai-output) | 签名 URL + 过期时间 | 产物可归档,定期清理[^5] |
| 可公开示例/素材 | 公开桶(如 public-assets) | 公开读取策略 | 明确公开范围与缓存策略[^5] |
| 批处理大文件 | 私有冷存桶 | 受控下载 | 限速、并发控制与审计[^5] |

上传方式上,建议优先采用 Edge Function 作为受控后端路径:客户端将文件通过 Edge Function 上传,函数侧完成鉴权、MIME 校验、病毒扫描、路径映射与数据库元数据登记。少用或避免将 service_role 暴露给客户端,以免绕过 RLS 与最小权限原则。[^5]

表 4:上传方式对比

| 上传路径 | 安全性 | 复杂度 | 适用场景 | 备注 |
|---|---|---|---|---|
| 客户端直传(带签名) | 中 | 低 | 低风险公开素材 | 需严格签名与策略校验[^24] |
| Edge Function 代理 | 高 | 中 | 敏感数据与受控写入 | 结合 RLS 与审计日志[^5] |
| 受保护后端 API | 高 | 中高 | 企业级集成 | 可做更复杂的合规检查[^5] |

路径命名是工程实践的高频“坑”。Supabase Storage 要求路径(桶名与对象名)使用 ASCII 字符;非 ASCII(如中文、日文、俄文等)会导致 InvalidKey 错误。务必在 Edge Function 中建立“本地化输入到规范化路径”的映射(例如将“日本”映射为“japan”),并统一文件名生成策略(时间戳前缀 + 随机后缀)以降低重名与冲突概率。[^5]

为降低“能传不能读”或“策略拒绝”的集成问题,建议在业务表与 storage.objects 上同时配置访问策略,并在函数写库时校验返回码与错误信息。

表 5:RLS 策略常见错误与修复

| 症状 | 根因 | 修复建议 |
|---|---|---|
| 新行违反 RLS 策略 | 仅允许 service_role,未包含 anon | 允许 auth.role() IN ('anon','service_role'),或在函数调用处显式传调用者身份[^7] |
| 公开文件读取失败 | 缺 storage.objects SELECT 策略 | 为目标桶增加 SELECT USING(bucket_id = '…')[^5] |
| 策略覆盖范围不清 | 使用 FOR ALL 导致误伤 | 按 SELECT/INSERT/UPDATE/DELETE 拆分策略[^25] |

### 受控上传与密钥管理

任何上传与分发路径,均不应在前端暴露 service_role。推荐以 Edge Function 作为“受控网关”:函数侧从环境变量读取密钥,完成鉴权、参数校验、路径归一与上传后元数据登记;返回给客户端的是最小必要的可见信息(例如公共域内可见的 URL 或受控的临时链接)。所有写入操作与错误均应记录审计日志,以支持后续追溯与合规检查。[^5]

### 路径与命名规范

路径策略建议遵循:

- 仅使用 ASCII 字符;中文、日文等输入在服务端映射为英文标签或哈希。
- 使用层级前缀进行分类(例如 type/date/id.jpg)。
- 文件名以“时间戳-随机字符串.ext”生成,避免重名与可猜测路径。
- 严格校验 MIME 类型与文件头,避免“伪装文件”绕过安全边界。[^5]

---

## 数据库设计与 AI 表结构:pgvector、检索与性能优化

面向 AI 的数据设计,核心在于对“语料/文档/消息/向量/元数据/权限”的抽象建模与高效检索。Supabase 基于 PostgreSQL,天然具备 SQL 能力、扩展生态与 RLS 优势;在 AI 检索侧,以 pgvector 扩展承载嵌入与相似度搜索,可与自查询检索器(Self-Query Retriever)等框架结合,实现语义与属性过滤的融合检索。[^8][^9][^10][^11][^14]

表 6:AI 应用关键表结构建议

| 表 | 关键字段 | 类型/约束 | 索引建议 | 说明 |
|---|---|---|---|---|
| documents | id, content, metadata, embedding | uuid, text, jsonb, vector(1536) | ivfflat/HNSW(向量)、GIN(metadata) | 文档语料与向量索引[^10][^14] |
| conversations | id, user_id, title, created_at | uuid, uuid, text, timestamptz | BTREE(user_id, created_at) | 会话/线程归集 |
| messages | id, conversation_id, role, content, created_at | uuid, uuid, text, text, timestamptz | BTREE(conversation_id, created_at) | 角色化对话 |
| runs/tasks | id, user_id, status, progress, error, created_at | uuid, uuid, enum, int, text, timestamptz | BTREE(user_id, created_at) | 任务与进度 |
| ai_outputs | id, task_id, type, uri, meta, created_at | uuid, uuid, enum, text, jsonb, timestamptz | BTREE(task_id, created_at) | AI 产物归档 |

向量检索方面,结合典型应用场景给出速查表:

表 7:向量检索操作速查

| 操作 | SQL 片段或查询要点 | 说明 |
|---|---|---|
| 相似度搜索 | ORDER BY embedding <=> query_embedding LIMIT k | 基于欧氏距离返回最近邻[^14] |
| 过滤检索 | 结合 WHERE metadata @> '{"tag":"value"}' | 利用 GIN 索引过滤元数据[^9] |
| 分页 | 结合 ORDER BY + LIMIT/OFFSET 或 keyset pagination | 避免深度 OFFSET 性能劣化[^9] |

RLS 模式建议以 auth.uid() 为数据归属边界,提供“本人可读、可写;团队共享按需放宽”的策略,并为公共数据另设只读通道(例如只允许 SELECT)。函数与触发器可用于自动设置 created_by、updated_at 等审计字段。性能优化方面,除了索引与分页策略,亦需关注热点列统计信息与执行计划的定期审查。[^7][^9][^25]

### 向量与元数据建模

建议以“content + metadata + embedding”的三段式结构组织 documents:content 承载原始文本或摘录;metadata 以 jsonb 存储来源、标签、权限与处理状态;embedding 使用适配模型维度的向量类型(例如 OpenAI 常见 1536 维)。pgvector 扩展提供多种索引类型与距离度量,ivfflat 与 HNSW 分别在不同数据规模与查询延迟目标下具备优势,需结合数据集规模与 QPS 目标进行权衡与实测。[^10][^14]

### 查询与性能优化

向量检索常与元数据过滤组合使用:先以向量距离缩小候选集,再以 JSONB @> 进行精准过滤,并通过合适的 LIMIT 控制返回大小。分页建议使用 keysetpagination(基于游标字段)以避免深度 OFFSET 带来的扫描开销。RLS 策略对性能有直接影响:避免在策略中使用复杂子查询与高基数函数;必要时可考虑以物化视图或冗余列的方式换取查询可读性与执行计划稳定。[^25]

---

## Edge Functions 在 AI API 调用中的使用:安全代理与流式响应

当应用需要调用第三方 AI(如大语言模型或嵌入服务)时,建议通过 Edge Functions 作为受控代理:在前端与第三方服务之间增加一层可审计、可限流、可重试的安全网关。函数侧以环境变量保存密钥,统一处理鉴权、参数校验、错误捕获与日志记录;对于聊天类应用,可在函数内实现流式响应的中转(SSE 或分块传输),以获得更好的交互体验。[^16][^17][^18][^19]

表 8:Edge Functions 常见错误与修复

| 症状 | 根因 | 修复建议 |
|---|---|---|
| new row violates row-level security policy | RLS 仅允许 service_role | 允许 auth.role() IN ('anon','service_role'),或在函数中明确调用者身份评估策略[^7] |
| Storage InvalidKey | 路径含非 ASCII 字符 | 在函数中做路径映射与文件名规范化[^5] |
| 500:模型调用失败 | 上游 API 限流/超时/参数错误 | 指数退避重试、参数预校验、统一错误包装与告警[^16][^17] |
| CORS 预检失败 | 跨域策略不完整 | 返回 OPTIONS,设置允许的源/头/方法与缓存时长[^16] |

### 受控调用与密钥保护

- 密钥保管:AI 厂商密钥、数据库高权限密钥等均置于函数环境变量中,绝不下发前端。
- 调用参数校验:对 model、max_tokens、temperature 等参数设定白名单与上下限,避免Prompt注入与参数越权。
- 重试与幂等:对瞬时网络错误与 429 使用指数退避;以幂等键(如请求摘要哈希)在数据库中记录已处理的请求,避免重复写入。[^16][^17]

### 流式响应与错误处理

聊天与生成场景建议在 Edge Function 内实现分块或 SSE 中转:将第三方模型的流式输出以合理的帧格式转发到前端,提升端到端首字节时间与可用性感知。错误处理层面,需要统一错误码与堆栈分级(应用错误/网络错误/第三方错误),在前端以差异化 UI 呈现;同时记录请求 ID、耗时与模型版本,便于问题定位与审计。[^16][^18]

---

## 实时功能与 AI 应用状态管理:Realtime、Presence 与事件广播

AI 应用中存在大量“长时任务”与“多端同步”场景:例如文档解析、嵌入生成、批量图像处理等。使用 Realtime 可以以低耦合的方式广播任务状态,利用 Presence 跟踪在线协作与会话参与情况,并通过数据库变更订阅实现界面与数据状态同步。[^20][^21][^22]

表 9:Realtime 用例与通道设计

| 用例 | 频道模型 | 事件设计 | 说明 |
|---|---|---|---|
| 聊天 | conversation:{id} | user_joined/typing/message_new | 消息事件 + 参与状态[^22] |
| 协作 | doc:{id} | cursor_update/lock_change | 光标/锁定广播,避免冲突[^21] |
| 批处理进度 | job:{id} | progress_update/completed | 进度百分比与状态机变迁[^20] |

Presence 机制基于 Phoenix Presence 的思想实现,提供 join/leave 与 state 同步能力,并支持自定义元数据(如角色、权限)。在实践中,务必实现“发布节流与合并”以减少无效刷屏:例如 progress_update 事件以 500ms 为窗口聚合最新百分比;对瞬时高频的 cursor 事件进行抽样或去抖。[^21][^20]

### 频道与事件设计

- 会话:以 conversation:{id} 为基本单元,标准化事件语义(user_joined、typing、message_new)。
- 协作:以 doc:{id} 为共享状态,定义 cursor、selection 与 lock_change 事件,并与 UI 组件解耦。
- 批处理:以 job:{id} 承载状态机(running/paused/completed/failed),确保进度、耗时与错误信息的完整广播。[^22]

### 状态一致性与断线重连

- 去重与一致性:消息与事件带序号或时间戳,客户端按序消费并在断线后进行补偿同步。
- 节流与合并:高频事件以窗口合并,避免 UI 抖动与性能问题。
- 重连策略:指数退避 + 心跳检测;必要时以“最后状态快照”快速恢复 UI,再增量补齐。[^20][^21]

---

## 性能优化与安全考虑:RLS 性能、密钥管理与合规

性能与安全是一体两面:没有安全的性能没有意义,没有性能的安全难以落地。对 Supabase + AI 的组合而言,优化路径集中在“索引与分页”“RLS 策略简化与复用”“密钥与凭证管理”“审计与合规”。[^25][^23][^26][^27]

表 10:RLS 性能优化清单

| 问题症状 | 诊断方法 | 优化措施 |
|---|---|---|
| 命中策略后查询变慢 | explain/analyze、收集统计信息 | 减少策略中复杂函数;为过滤列加 B/GIN 索引;避免隐式类型转换[^25] |
| 高基数下误用子查询 | 执行计划异常、IO 膨胀 | 将复杂子查询下沉为物化视图或预计算列[^25] |
| 写路径受策略阻塞 | 观察错误与重试 | 为 Edge Functions 明确 anon/service_role 授权;写后验证并记录审计[^7] |

表 11:安全配置核对清单

| 类别 | 核对项 | 说明 |
|---|---|---|
| 密钥 | Edge Functions 环境变量 | 所有 AI 与高权限密钥置于函数侧;绝不下发前端[^23] |
| 认证 | MFA 与回调域校验 | 高价值操作强制 MFA;回调与重定向白名单[^6][^23] |
| RLS | 最小权限与角色分离 | SELECT/INSERT/UPDATE/DELETE 拆分;按数据归属建模[^7][^23] |
| 存储 | 默认私有 + 签名 URL | 非必要不公开;公开桶仅限公开素材并可撤销[^5][^24] |
| 审计 | 错误与访问日志 | 统一错误码与追踪 ID;日志保留与合规归档[^23] |

安全层面,建议以“凭证最小化 + 访问路径最小化”为原则:函数代理调用第三方 AI;前端不持有任何高权限密钥;RLS 策略按操作与归属拆分;数据与事件日志统一纳管并保留足够时长,以满足法务与合规要求。[^23][^26][^27]

---

## 实施清单与常见错误:部署前检查与问题定位

将“最佳实践”转化为“上线清单”,是降低返工与故障的关键一环。

表 12:上线前检查清单

| 模块 | 核对项 | 验收要点 |
|---|---|---|
| 认证 | 前端 getUser + 回调守卫 | 登录/登出状态一致,路由守卫正确拦截[^6] |
| 存储 | 路径 ASCII 化 + 桶与策略 | InvalidKey 为零;仅公开必要前缀[^5] |
| RLS | 业务表 + storage.objects | SELECT/INSERT 策略覆盖 anon;写库成功[^7] |
| Edge Functions | CORS + 错误码统一 | OPTIONS 返回正确;上游错误有分级与告警[^16] |
| Realtime | 频道设计 + 节流策略 | 高频事件合并;断线重连一致[^20][^21] |
| 性能 | 索引与分页 | explain/analyze 无异常;TOP 查询稳定[^25] |

常见错误的快速定位方法:

- RLS 策略拒绝:检查 auth.role() 与 anon 覆盖;将策略按操作拆分;观察错误消息的表与操作类型。[^7]
- Storage InvalidKey:统一在函数内做本地化到 ASCII 的路径映射;文件名规范化。[^5]
- 模型调用错误:校验参数白名单、上游限流与超时;统一错误包装与重试策略;记录请求 ID 便于追踪。[^16][^17]

---

## 结论与战略建议:可扩展架构与未来演进

在以 Supabase 为核心的 AI 应用中,“认证与授权—存储—数据库—函数—实时—安全”的闭环提供了稳定的地基;在此之上,pgvector 支撑的语义检索与 Edge Functions 支撑的受控 AI 调用构成了智能层的主干。面向未来,建议从三个方向持续演进:

- 数据分层与湖仓化:将热点交互数据与冷数据分层,并评估与外部数据湖/仓库的联动,平衡成本与性能。[^8]
- 检索增强与多模型协同:结合自查询检索器与多路召回策略,探索模型路由与成本/质量平衡,逐步形成企业级的“模型中台”。[^14][^16][^17]
- 安全与合规左移:将审计、渗透测试与策略审计纳入日常开发流程,形成“可证明的安全”,并引入自动化审计工具链辅助策略修复与验证。[^23][^26][^27]

通过本蓝图的工程化落地,团队能够以“最小必要复杂度”实现从 0 到 1 的 AI 应用交付,并具备在 1 到 N 阶段持续演进的能力。

---

## 信息缺口与后续研究计划

- CDN 层面(缓存策略、区域分发、对象生命周期管理)的官方细则与参数未在现有上下文中覆盖,需结合最新官方文档与运营数据补充。
- 不同 pgvector 索引类型(ivfflat/HNSW 等)在特定硬件与数据规模下的定量性能对比尚缺,需基于目标环境进行基准测试与调参。
- AI 应用在行业合规(数据跨境、审计留痕、MFA 策略细则)的落地案例需要更多一线项目数据支持。
- Edge Functions 的并发、内存与冷启动成本模型缺少精确指标,建议在生产流量下开展长期观测与容量规划。
- Realtime 在大规模 Presence 与高频广播下的网络开销与断线重连策略缺少量化指标,需灰度验证与自适应调优。

---

## 参考文献

[^1]: Supabase Docs(官方文档总览). https://supabase.com/docs  
[^2]: Supabase 架构总览. https://supabase.com/docs/guides/getting-started/architecture  
[^3]: Supabase 功能一览. https://supabase.com/features  
[^4]: Database | Supabase Docs(数据库总览). https://supabase.com/docs/guides/database/overview  
[^5]: Storage | Supabase Docs. https://supabase.com/docs/guides/storage  
[^6]: Auth | Supabase Docs. https://supabase.com/docs/guides/auth  
[^7]: Row Level Security | Supabase Docs. https://supabase.com/docs/guides/database/postgres/row-level-security  
[^8]: Database | Open source SQL Database(产品页). https://supabase.com/database  
[^9]: PostgreSQL 官方文档. https://www.postgresql.org/docs/  
[^10]: pgvector README. https://github.com/pgvector/pgvector  
[^11]: LangChain GitHub. https://github.com/langchain-ai/langchain  
[^12]: 使用 Supabase 和 Postgres 构建智能 AI 应用程序(pgvector 实践). https://juejin.cn/post/7427455855941845004  
[^13]: Building AI-Powered Apps with Supabase in 2025. https://scaleupally.io/blog/building-ai-app-with-supabase/  
[^14]: Standard Uploads | Supabase Docs. https://supabase.com/docs/guides/storage/uploads/standard-uploads  
[^15]: Running AI Models | Supabase Docs. https://supabase.com/docs/guides/functions/ai-models  
[^16]: Generating OpenAI GPT3 completions | Supabase Docs. https://supabase.com/docs/guides/ai/examples/openai  
[^17]: burggraf/openai-supabase-edge-functions. https://github.com/burggraf/openai-supabase-edge-functions  
[^18]: Building a ChatGPT Clone with Supabase Edge Functions and OpenAI. https://nikofischer.com/building-chatgpt-clone-supabase-edge-functions  
[^19]: Supabase Realtime(开源服务器). https://github.com/supabase/realtime  
[^20]: Supabase 实时功能:构建现代 Web 应用(CSDN). https://blog.csdn.net/gitblog_00088/article/details/148323275  
[^21]: Supabase Realtime Presence 功能实战(CSDN). https://blog.csdn.net/gitblog_01151/article/details/154423224  
[^22]: Pricing & Fees | Supabase. https://supabase.com/pricing  
[^23]: 2025 Supabase Security Best Practices Guide(官方讨论). https://github.com/orgs/supabase/discussions/38690  
[^24]: Supabase RLS Security Audit and Fixes with MCP. https://docs.continue.dev/guides/supabase-mcp-database-workflow  
[^25]: RLS Performance and Best Practices | Supabase. https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv  
[^26]: Optimizing RLS Performance with Supabase. https://www.antstack.com/blog/optimizing-rls-performance-with-supabase/