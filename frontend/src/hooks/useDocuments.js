import { useCallback, useEffect, useState } from "react";
import { getErrorMessage } from "../api/client";
import * as documentsApi from "../api/documents";

/** Loads the user's documents and exposes reload/remove helpers. */
export default function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const reload = useCallback(async () => {
    try {
      setError("");
      setDocuments(await documentsApi.listDocuments());
    } catch (err) {
      setError(getErrorMessage(err, "Could not load your documents."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const remove = useCallback(async (id) => {
    await documentsApi.deleteDocument(id);
    setDocuments((docs) => docs.filter((d) => d.id !== id));
  }, []);

  return { documents, loading, error, reload, remove };
}
