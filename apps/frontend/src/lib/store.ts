import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthUser {
  userId: string;
  firstName: string;
  role: "user" | "admin";
}

interface AuthStore {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  setUser: (user: AuthUser | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isAdmin: false,

      setUser: (user) =>
        set({
          user,
          isAuthenticated: !!user,
          isAdmin: user?.role === "admin",
        }),

      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          isAdmin: false,
        }),
    }),
    {
      name: "sf_auth",
      partialize: (state) => ({ user: state.user }),
    }
  )
);
