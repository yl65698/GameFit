import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original?._retry) {
      return Promise.reject(error);
    }

    const refresh = localStorage.getItem("refreshToken");
    if (!refresh) {
      clearAuthStorage();
      return Promise.reject(error);
    }

    original._retry = true;
    try {
      const { data } = await axios.post(`${api.defaults.baseURL}/accounts/token/refresh/`, { refresh });
      localStorage.setItem("accessToken", data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (refreshError) {
      clearAuthStorage();
      return Promise.reject(refreshError);
    }
  },
);

export function clearAuthStorage() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("authToken");
  localStorage.removeItem("authUser");
}

export default api;
