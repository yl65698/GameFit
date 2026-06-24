import { defineStore } from "pinia";

import api, { clearAuthStorage } from "../services/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("accessToken") || "",
    refreshToken: localStorage.getItem("refreshToken") || "",
    user: readStoredUser(),
    loading: false,
    error: "",
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    persist(payload) {
      this.token = payload.access;
      this.refreshToken = payload.refresh;
      this.user = payload.user;
      localStorage.setItem("accessToken", payload.access);
      localStorage.setItem("refreshToken", payload.refresh);
      localStorage.setItem("authUser", JSON.stringify(payload.user));
    },
    async signup(form) {
      this.loading = true;
      this.error = "";
      try {
        const { data } = await api.post("/accounts/signup/", form);
        this.persist(data);
        return data;
      } catch (error) {
        this.error = normalizeError(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async login(form) {
      this.loading = true;
      this.error = "";
      try {
        const { data } = await api.post("/accounts/login/", form);
        this.persist(data);
        return data;
      } catch (error) {
        this.error = normalizeError(error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async fetchProfile() {
      if (!this.token) return null;
      try {
        const { data } = await api.get("/accounts/profile/");
        this.user = data;
        localStorage.setItem("authUser", JSON.stringify(data));
        return data;
      } catch (error) {
        if (error.response?.status === 401) {
          this.clearSession();
        }
        throw error;
      }
    },
    async updateProfile(profile) {
      const { data } = await api.patch("/accounts/profile/", profile);
      this.user = data;
      localStorage.setItem("authUser", JSON.stringify(data));
      return data;
    },
    async uploadProfileImage(file) {
      const formData = new FormData();
      formData.append("profile_image", file);
      const { data } = await api.patch("/accounts/profile/", formData);
      this.user = data;
      localStorage.setItem("authUser", JSON.stringify(data));
      return data;
    },
    async followUser(userId) {
      const { data } = await api.post(`/accounts/users/${userId}/follow/`);
      return data;
    },
    async fetchUserByUsername(username) {
      const { data } = await api.get(`/accounts/users/by-username/${username}/`);
      return data;
    },
    async searchUsers(query) {
      const { data } = await api.get("/accounts/users/search/", { params: { q: query } });
      return data;
    },
    async logout() {
      try {
        if (this.token) {
          await api.post("/accounts/logout/");
        }
      } finally {
        this.clearSession();
      }
    },
    clearSession() {
      this.token = "";
      this.refreshToken = "";
      this.user = null;
      clearAuthStorage();
    },
  },
});

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("authUser") || "null");
  } catch {
    clearAuthStorage();
    return null;
  }
}

function normalizeError(error) {
  const data = error.response?.data;
  if (!data) return "요청 중 오류가 발생했습니다.";
  if (typeof data === "string") return data;
  if (Array.isArray(data)) return data.join(" ");
  return Object.values(data).flat().join(" ");
}
