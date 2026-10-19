import api from "./client";

export const listDocuments = () => api.get("/documents/").then((r) => r.data.results);

export const uploadDocument = (file, onProgress) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post("/documents/upload/", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded * 100) / e.total)),
    })
    .then((r) => r.data);
};

export const deleteDocument = (id) => api.delete(`/documents/${id}/`);
