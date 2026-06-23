import axios from "axios";

const aiApi = axios.create({
  baseURL: import.meta.env.VITE_AI_API_BASE_URL || "http://127.0.0.1:8002",
});

export default aiApi;
