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
  try {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
  } catch { /* localStorage unavailable */ }
  return config;
});

api.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const { data } = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
          localStorage.setItem("access_token", data.access_token);
          if (data.refresh_token) {
            localStorage.setItem("refresh_token", data.refresh_token);
          }
          original.headers["Authorization"] = `Bearer ${data.access_token}`;
          return api(original);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
    return Promise.reject(error);
  },
);

export default api;
