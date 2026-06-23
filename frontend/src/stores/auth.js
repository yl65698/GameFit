import { defineStore } from "pinia";

import api from "../services/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("authToken") || "",
    user: readStoredUser(),
    loading: false,
    error: "",
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    persist(payload) {
      this.token = payload.token;
      this.user = payload.user;
      localStorage.setItem("authToken", payload.token);
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
      this.user = null;
      localStorage.removeItem("authToken");
      localStorage.removeItem("authUser");
    },
  },
});

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("authUser") || "null");
  } catch {
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUser");
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
