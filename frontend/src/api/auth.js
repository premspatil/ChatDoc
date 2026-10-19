import api from "./client";

export const register = (payload) => api.post("/auth/register/", payload).then((r) => r.data);
export const login = (payload) => api.post("/auth/login/", payload).then((r) => r.data);
export const logout = () => api.post("/auth/logout/");
export const getMe = () => api.get("/auth/me/").then((r) => r.data);
