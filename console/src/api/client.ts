import axios from "axios";

const API_KEY = import.meta.env.VITE_API_KEY || "";

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (API_KEY) {
    config.headers["X-API-Key"] = API_KEY;
  }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("API Key 无效或未配置");
    }
    return Promise.reject(error);
  },
);

export default api;
