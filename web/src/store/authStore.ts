import { create } from "zustand";
import { persist } from "zustand/middleware";
import Cookies from "js-cookie";

interface AuthState {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: any) => void;
  logout: () => void;
}

const GUEST_USER = { id: "d74c3017-3383-48fd-bc25-094475534748", name: "Guest User", email: "guest@nutrimind.app" };
const GUEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNzRjMzAxNy0zMzgzLTQ4ZmQtYmMyNS0wOTQ0NzU1MzQ3NDgiLCJleHAiOjE3ODI0MDY1MDAsImlhdCI6MTc3OTgxNDUwMCwidHlwZSI6ImFjY2VzcyJ9.UbR-6LSY1xKtVbM4-nWzavDyyAToaT2m2n_JfvMqk3U";

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: GUEST_TOKEN,
      user: GUEST_USER,
      isAuthenticated: true,
      setAuth: (token, user) => {
        Cookies.set("access_token", token, { expires: 7, sameSite: "strict" });
        localStorage.setItem("access_token", token);
        set({ token, user, isAuthenticated: true });
      },
      logout: () => {
        Cookies.remove("access_token");
        localStorage.removeItem("access_token");
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    { name: "nutrimind-auth", partialize: (s) => ({ token: s.token, user: s.user, isAuthenticated: s.isAuthenticated }) }
  )
);
