import axios from "axios";

const TOKEN_KEY = "chatdoc_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  timeout: 120000, // PDF processing can take a while on the first run (model download)
});

// Attach the login token to every request.
api.interceptors.request.use((config) => {
  const token = tokenStore.get();
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

// If the token is no longer valid, log the user out.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || "";
    const isAuthCall = url.includes("/auth/login") || url.includes("/auth/register");
    if (error.response?.status === 401 && !isAuthCall) {
      tokenStore.clear();
      window.dispatchEvent(new Event("chatdoc:logout"));
    }
    return Promise.reject(error);
  }
);

/** Turn any API error into one short, user-friendly sentence. */
export function getErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  if (!error.response) {
    return error.code === "ECONNABORTED"
      ? "The request timed out. Please try again."
      : "Cannot reach the server. Is the backend running?";
  }
  const data = error.response.data;
  if (data?.details && typeof data.details === "object") {
    const first = Object.values(data.details).flat()[0];
    if (typeof first === "string") return first;
  }
  return data?.error || fallback;
}

export default api;
