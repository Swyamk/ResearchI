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

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
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
