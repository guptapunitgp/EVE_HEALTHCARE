import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? "http://localhost:8000" : "https://eve-healthcare-iqyd.onrender.com");

const api = axios.create({
  baseURL: `${apiBaseUrl.replace(/\/$/, "")}/api/v1`,
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("eve_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes("/auth/firebase")) {
      sessionStorage.removeItem("eve_token");
      if (window.location.pathname.startsWith("/app") || window.location.pathname.startsWith("/staff") || window.location.pathname.startsWith("/admin")) {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);

export const unwrap = (value) => value?.items ?? value ?? [];
export default api;
