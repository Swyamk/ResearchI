import axios from "axios";
import Cookies from "js-cookie";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

const GUEST_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNzRjMzAxNy0zMzgzLTQ4ZmQtYmMyNS0wOTQ0NzU1MzQ3NDgiLCJleHAiOjE3ODI0MDY1MDAsImlhdCI6MTc3OTgxNDUwMCwidHlwZSI6ImFjY2VzcyJ9.UbR-6LSY1xKtVbM4-nWzavDyyAToaT2m2n_JfvMqk3U";

function getToken(): string {
  if (typeof window === "undefined") return GUEST_TOKEN;
  const direct = Cookies.get("access_token") || localStorage.getItem("access_token");
  if (direct) return direct;
  try {
    const persisted = localStorage.getItem("nutrimind-auth");
    const stored = JSON.parse(persisted ?? "")?.state?.token;
    if (stored) return stored;
  } catch { /* ignore */ }
  return GUEST_TOKEN;
}

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally — auth barrier disabled, ignore 401s
api.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err)
);

export default api;
