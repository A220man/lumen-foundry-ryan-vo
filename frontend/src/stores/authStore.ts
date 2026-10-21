import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  isAuthenticated: boolean;
  user: { id: string; email: string; name: string; roles: string[] } | null;
  accessToken: string | null;
  login: (token: string, user: { id: string; email: string; name: string; roles: string[] }) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,

      login: (token, user) => {
        localStorage.setItem('access_token', token);
        set({ isAuthenticated: true, user, accessToken: token });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ isAuthenticated: false, user: null, accessToken: null });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.exp * 1000 > Date.now()) {
              set({
                isAuthenticated: true,
                user: {
                  id: payload.sub,
                  email: payload.email,
                  name: payload.preferred_username || payload.name,
                  roles: payload.realm_access?.roles || [],
                },
                accessToken: token,
              });
              return;
            }
          } catch {
          }
        }
        set({ isAuthenticated: false, user: null, accessToken: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        accessToken: state.accessToken,
      }),
    }
  )
);
