import api from "./client";

export interface TypeDef {
  api_name: string;
  type: string;
  display_name: string;
  description: string;
  config: Record<string, unknown>;
  maturity: string;
  created_at: string;
  updated_at: string;
}

export const fetchTypes = (type?: string) =>
  api.get<TypeDef[]>("/types", { params: type ? { type } : {} }).then((r) => r.data);

export const fetchType = (apiName: string) =>
  api.get<TypeDef>(`/types/${apiName}`).then((r) => r.data);

export const createType = (data: Record<string, unknown>) =>
  api.post<TypeDef>("/types", data).then((r) => r.data);

export const updateType = (apiName: string, data: Record<string, unknown>) =>
  api.put<TypeDef>(`/types/${apiName}`, data).then((r) => r.data);

export const deleteType = (apiName: string) =>
  api.delete(`/types/${apiName}`);

export interface ObjectInstance {
  id: string;
  object_type: string;
  external_id: string;
  dataset_id: string;
  display_name: string;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export const fetchObjects = (params?: Record<string, unknown>) =>
  api.get<{ data: ObjectInstance[]; total: number; page: number; size: number }>("/objects", { params }).then((r) => r.data);

export const searchObjects = (q: string) =>
  api.get<ObjectInstance[]>("/objects/search", { params: { q } }).then((r) => r.data);

export const createObject = (data: Record<string, unknown>) =>
  api.post<ObjectInstance>("/objects", data).then((r) => r.data);

export const deleteObject = (id: string) =>
  api.delete(`/objects/${id}`);

export interface GraphData {
  nodes: Array<{ id: string; label: string; [key: string]: unknown }>;
  edges: Array<{ id: string; source: string; target: string; label: string; [key: string]: unknown }>;
}

export const fetchStructureGraph = () =>
  api.get<GraphData>("/graph/structure").then((r) => r.data);

export const fetchEntityGraph = (dataset?: string) =>
  api.get<GraphData>("/graph/entities", { params: { dataset: dataset || "default" } }).then((r) => r.data);

export const fetchStats = () =>
  api.get<Record<string, number>>("/stats").then((r) => r.data);

export const fetchLinks = (dataset?: string) =>
  api.get("/links", { params: dataset ? { dataset } : {} }).then((r) => r.data);

export const createLink = (data: Record<string, unknown>) =>
  api.post("/links", data).then((r) => r.data);

export const deleteLink = (id: string) =>
  api.delete(`/links/${id}`);

export const fetchActionHistory = (page = 1, size = 20) =>
  api.get<{ data: unknown[]; total: number; page: number; size: number }>("/actions/history", { params: { page, size } }).then((r) => r.data);

// ── Phase B: 批量操作 ──

export const batchCreateObjects = (items: Record<string, unknown>[]) =>
  api.post("/objects/batch/create", { items }).then((r) => r.data);

export const batchCreateLinks = (items: Record<string, unknown>[]) =>
  api.post("/links/batch/create", { items }).then((r) => r.data);

// ── Phase B: 高级图谱 ──

export interface PathResult {
  found: boolean;
  path: Array<{ id: string; label: string; type: string }>;
  edges: string[];
  length: number;
}

export const findPath = (source: string, target: string, dataset = "default", maxDepth = 5) =>
  api.get<PathResult>("/graph/path", { params: { source, target, dataset, max_depth: maxDepth } }).then((r) => r.data);

export const getNeighbors = (node: string, dataset = "default", direction = "both") =>
  api.get("/graph/neighbors", { params: { node, dataset, direction } }).then((r) => r.data);

export const traverseGraph = (start: string, dataset = "default", maxDepth = 3, strategy = "bfs") =>
  api.get("/graph/traverse", { params: { start, dataset, max_depth: maxDepth, strategy } }).then((r) => r.data);

export const fetchGraphStats = (dataset = "default") =>
  api.get("/graph/stats", { params: { dataset } }).then((r) => r.data);

// ── Phase B: 属性定义 ──

export const updateTypeProperties = (apiName: string, properties: Record<string, unknown>[]) =>
  api.patch(`/types/${apiName}/properties`, properties).then((r) => r.data);

// ── Phase B: 暂存工作流 ──

export const storeChange = (data: Record<string, unknown>) =>
  api.post("/staging/store", data).then((r) => r.data);

export const commitChanges = (ids?: string[], all?: boolean) =>
  api.post("/staging/commit", { ids, all }).then((r) => r.data);

export const discardChanges = (ids?: string[], all?: boolean) =>
  api.delete("/staging/discard", { data: { ids, all } }).then((r) => r.data);

export const revertChanges = (ids: string[]) =>
  api.post("/staging/revert", { ids }).then((r) => r.data);

export const fetchStagedChanges = (status?: string) =>
  api.get("/staging", { params: status ? { status } : {} }).then((r) => r.data);

// ── Phase B: 版本管理 ──

export const createSnapshot = (comment?: string) =>
  api.post("/versions/snapshot", null, { params: { comment } }).then((r) => r.data);

export const fetchVersions = () =>
  api.get("/versions").then((r) => r.data);

export const fetchVersion = (id: number) =>
  api.get(`/versions/${id}`).then((r) => r.data);

export const compareVersions = (base: number, target: number) =>
  api.post("/versions/compare", null, { params: { base, target } }).then((r) => r.data);

export const rollbackVersion = (id: number) =>
  api.post(`/versions/rollback/${id}`).then((r) => r.data);

// ── Phase B: ACR 访问控制 ──

export const fetchAcrRules = () =>
  api.get("/acr/rules").then((r) => r.data);

export const createAcrRule = (data: Record<string, unknown>) =>
  api.post("/acr/rules", data).then((r) => r.data);

export const deleteAcrRule = (id: number) =>
  api.delete(`/acr/rules/${id}`);

export const fetchAcrGroups = () =>
  api.get("/acr/groups").then((r) => r.data);

export const createAcrGroup = (data: Record<string, unknown>) =>
  api.post("/acr/groups", data).then((r) => r.data);

export const fetchAcrBindings = (userId?: string) =>
  api.get("/acr/bindings", { params: userId ? { user_id: userId } : {} }).then((r) => r.data);

export const createAcrBinding = (data: Record<string, unknown>) =>
  api.post("/acr/bindings", data).then((r) => r.data);

export const evaluateAccess = (data: Record<string, unknown>) =>
  api.post("/acr/evaluate", data).then((r) => r.data);

// ── Auth: JWT 认证 ──

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export const login = (data: LoginRequest) =>
  api.post<TokenResponse>("/auth/login", data).then((r) => r.data);

export const refreshToken = (refreshToken: string) =>
  api.post<TokenResponse>("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data);

export const logout = () =>
  api.post("/auth/logout");

export const fetchProfile = () =>
  api.get<UserProfile>("/auth/profile").then((r) => r.data);

export const changePassword = (data: { old_password: string; new_password: string }) =>
  api.put("/auth/password", data).then((r) => r.data);

// ── Admin: 用户/角色/组管理 ──

export const fetchUsers = () =>
  api.get("/admin/users").then((r) => r.data);

export const createUser = (data: Record<string, unknown>) =>
  api.post("/admin/users", data).then((r) => r.data);

export const updateUser = (userId: string, data: Record<string, unknown>) =>
  api.put(`/admin/users/${userId}`, data).then((r) => r.data);

export const deleteUser = (userId: string) =>
  api.delete(`/admin/users/${userId}`);

export const fetchRoles = () =>
  api.get("/admin/roles").then((r) => r.data);

export const createRole = (data: Record<string, unknown>) =>
  api.post("/admin/roles", data).then((r) => r.data);

export const updateRole = (roleId: string, data: Record<string, unknown>) =>
  api.put(`/admin/roles/${roleId}`, data).then((r) => r.data);

export const deleteRole = (roleId: string) =>
  api.delete(`/admin/roles/${roleId}`);

export const assignRole = (userId: string, roleId: string) =>
  api.post(`/admin/users/${userId}/roles`, { role_id: roleId }).then((r) => r.data);

export const removeRole = (userId: string, roleId: string) =>
  api.delete(`/admin/users/${userId}/roles/${roleId}`);

export const fetchUserRoles = (userId: string) =>
  api.get(`/admin/users/${userId}/roles`).then((r) => r.data);

export const fetchGroups = () =>
  api.get("/admin/groups").then((r) => r.data);

export const createGroup = (data: Record<string, unknown>) =>
  api.post("/admin/groups", data).then((r) => r.data);

export const updateGroup = (groupId: string, data: Record<string, unknown>) =>
  api.put(`/admin/groups/${groupId}`, data).then((r) => r.data);

export const deleteGroup = (groupId: string) =>
  api.delete(`/admin/groups/${groupId}`);

export const addGroupMember = (groupId: string, userId: string) =>
  api.post(`/admin/groups/${groupId}/members`, { user_id: userId }).then((r) => r.data);

export const removeGroupMember = (groupId: string, userId: string) =>
  api.delete(`/admin/groups/${groupId}/members/${userId}`);

export const fetchGroupMembers = (groupId: string) =>
  api.get(`/admin/groups/${groupId}/members`).then((r) => r.data);

// ── Admin: API Key 管理 ──

export const fetchApiKeys = () =>
  api.get("/admin/api-keys").then((r) => r.data);

export const createApiKey = (data: Record<string, unknown>) =>
  api.post("/admin/api-keys", data).then((r) => r.data);

export const updateApiKey = (keyId: string, data: Record<string, unknown>) =>
  api.put(`/admin/api-keys/${keyId}`, data).then((r) => r.data);

export const deleteApiKey = (keyId: string) =>
  api.delete(`/admin/api-keys/${keyId}`);

// ── Auth: PAT 个人访问令牌 ──

export const fetchPats = () =>
  api.get("/auth/pat").then((r) => r.data);

export const createPat = (data: Record<string, unknown>) =>
  api.post("/auth/pat", data).then((r) => r.data);

export const deletePat = (patId: string) =>
  api.delete(`/auth/pat/${patId}`);

// ── Admin: 系统配置 ──

export const fetchPublicConfig = () =>
  api.get("/public-config").then((r) => r.data);

export const fetchSystemConfig = () =>
  api.get("/admin/config").then((r) => r.data);

export const updateSystemConfig = (key: string, value: unknown) =>
  api.put(`/admin/config/${key}`, { value }).then((r) => r.data);

// ── Phase C: 自动建模 ──

export const testDbConnection = (data: Record<string, unknown>) =>
  api.post("/auto-model/test-connection", data).then((r) => r.data);

export const fetchDatabases = () =>
  api.get("/auto-model/databases").then((r) => r.data);

export const fetchSchemas = () =>
  api.get("/auto-model/schemas").then((r) => r.data);

export const fetchTables = (schema?: string) =>
  api.get("/auto-model/tables", { params: schema ? { schema } : {} }).then((r) => r.data);

export const describeTable = (schema: string, table: string) =>
  api.get("/auto-model/describe-table", { params: { schema, table } }).then((r) => r.data);

export const analyzeTable = (data: Record<string, unknown>) =>
  api.post("/auto-model/analyze", data).then((r) => r.data);

export const quickAnalyze = (data: Record<string, unknown>) =>
  api.post("/auto-model/quick-analyze", data).then((r) => r.data);

export const validateModel = (data: Record<string, unknown>) =>
  api.post("/auto-model/validate", data).then((r) => r.data);

export const refineModel = (data: Record<string, unknown>) =>
  api.post("/auto-model/refine", data).then((r) => r.data);

export const syncModel = (data: Record<string, unknown>) =>
  api.post("/auto-model/sync", data).then((r) => r.data);

export const detectChanges = (data: Record<string, unknown>) =>
  api.post("/auto-model/detect-changes", data).then((r) => r.data);

// ── Phase C: Skills 技能系统 ──

export const fetchSkills = () =>
  api.get("/skills").then((r) => r.data);

export const fetchSkill = (skillId: string) =>
  api.get(`/skills/${skillId}`).then((r) => r.data);

export const createSkill = (data: Record<string, unknown>) =>
  api.post("/skills", data).then((r) => r.data);

export const updateSkill = (skillId: string, data: Record<string, unknown>) =>
  api.put(`/skills/${skillId}`, data).then((r) => r.data);

export const deleteSkill = (skillId: string) =>
  api.delete(`/skills/${skillId}`);

export const toggleSkill = (skillId: string) =>
  api.put(`/skills/${skillId}/toggle`).then((r) => r.data);

export const cloneSkill = (skillId: string) =>
  api.post(`/skills/${skillId}/clone`).then((r) => r.data);

export const exportSkill = (skillId: string) =>
  api.get(`/skills/export/${skillId}`).then((r) => r.data);

export const importSkill = (data: Record<string, unknown>) =>
  api.post("/skills/import", data).then((r) => r.data);

export const fetchSkillPresets = () =>
  api.get("/skills/presets").then((r) => r.data);

export const generateSkills = (datasetId: string) =>
  api.post(`/skills/datasets/${datasetId}/generate`).then((r) => r.data);

// ── Phase C: LLM 配置管理 ──

export const fetchLlmConfigs = () =>
  api.get("/llm-configs").then((r) => r.data);

export const fetchLlmConfig = (configId: string) =>
  api.get(`/llm-configs/${configId}`).then((r) => r.data);

export const createLlmConfig = (data: Record<string, unknown>) =>
  api.post("/llm-configs", data).then((r) => r.data);

export const updateLlmConfig = (configId: string, data: Record<string, unknown>) =>
  api.put(`/llm-configs/${configId}`, data).then((r) => r.data);

export const deleteLlmConfig = (configId: string) =>
  api.delete(`/llm-configs/${configId}`);

export const testLlmConnection = (configId: string) =>
  api.post(`/llm-configs/${configId}/test-connection`).then((r) => r.data);

// ── Phase C: 文档上传 ──

export const uploadDocument = (formData: FormData) =>
  api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);

export const fetchDocuments = () =>
  api.get("/documents").then((r) => r.data);

export const fetchDocument = (docId: string) =>
  api.get(`/documents/${docId}`).then((r) => r.data);

export const fetchDocumentText = (docId: string) =>
  api.get(`/documents/${docId}/text`).then((r) => r.data);

export const deleteDocument = (docId: string) =>
  api.delete(`/documents/${docId}`);

// ── 数据集管理 ──

export const fetchDatasets = () =>
  api.get("/datasets").then((r) => r.data);

export const createDataset = (data: Record<string, unknown>) =>
  api.post("/datasets", data).then((r) => r.data);

export const updateDataset = (datasetId: string, data: Record<string, unknown>) =>
  api.put(`/datasets/${datasetId}`, data).then((r) => r.data);

export const deleteDataset = (datasetId: string) =>
  api.delete(`/datasets/${datasetId}`);

// ── Phase D: 后台任务 ──

export const fetchTasks = () =>
  api.get("/tasks").then((r) => r.data);

export const fetchTask = (taskId: string) =>
  api.get(`/tasks/${taskId}`).then((r) => r.data);

export const cancelTask = (taskId: string) =>
  api.post(`/tasks/${taskId}/cancel`).then((r) => r.data);

export const fetchTaskLogs = (taskId: string) =>
  api.get(`/tasks/${taskId}/logs`).then((r) => r.data);

// ── Phase D: 文档引擎 ──

export const fetchDocEngineConfig = () =>
  api.get("/admin/doc-engine").then((r) => r.data);

export const updateDocEngineConfig = (data: Record<string, unknown>) =>
  api.put("/admin/doc-engine", data).then((r) => r.data);

export const testDocEngineConnection = () =>
  api.post("/admin/doc-engine/test-connection").then((r) => r.data);

// ── Phase D: RAG 评测 ──

export const fetchEvalDatasets = () =>
  api.get("/eval/datasets").then((r) => r.data);

export const createEvalDataset = (data: Record<string, unknown>) =>
  api.post("/eval/datasets", data).then((r) => r.data);

export const fetchEvalDataset = (datasetId: string) =>
  api.get(`/eval/datasets/${datasetId}`).then((r) => r.data);

export const updateEvalDataset = (datasetId: string, data: Record<string, unknown>) =>
  api.put(`/eval/datasets/${datasetId}`, data).then((r) => r.data);

export const deleteEvalDataset = (datasetId: string) =>
  api.delete(`/eval/datasets/${datasetId}`);

export const uploadEvalDataset = (formData: FormData) =>
  api.post("/eval/datasets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);

export const createEvalRun = (data: Record<string, unknown>) =>
  api.post("/eval/runs", data).then((r) => r.data);

export const fetchEvalRuns = () =>
  api.get("/eval/runs").then((r) => r.data);

export const fetchEvalRun = (runId: string) =>
  api.get(`/eval/runs/${runId}`).then((r) => r.data);

export const fetchEvalComparisons = () =>
  api.get("/eval/comparisons").then((r) => r.data);

// ── Phase D: OSS 对象存储 ──

export const fetchOssConfig = () =>
  api.get("/admin/oss").then((r) => r.data);

export const updateOssConfig = (data: Record<string, unknown>) =>
  api.put("/admin/oss", data).then((r) => r.data);

export const testOssConnection = () =>
  api.post("/admin/oss/test-connection").then((r) => r.data);
