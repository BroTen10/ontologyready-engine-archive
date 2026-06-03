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
