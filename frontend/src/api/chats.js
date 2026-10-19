import api from "./client";

export const listChats = () => api.get("/chats/").then((r) => r.data.results);
export const createChat = (documentId) =>
  api.post("/chats/", { document_id: documentId }).then((r) => r.data);
export const getChat = (id) => api.get(`/chats/${id}/`).then((r) => r.data);
export const deleteChat = (id) => api.delete(`/chats/${id}/`);
export const getMessages = (id) => api.get(`/chats/${id}/messages/`).then((r) => r.data);
export const clearMessages = (id) => api.delete(`/chats/${id}/messages/`);
export const askQuestion = (id, question) =>
  api.post(`/chats/${id}/ask/`, { question }).then((r) => r.data);
