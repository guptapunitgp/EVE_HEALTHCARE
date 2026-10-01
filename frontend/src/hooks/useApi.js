import { useEffect, useState } from "react";
import api, { unwrap } from "../lib/api";

export function useApi(path, refreshKey = 0) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let current = true;
    api.get(path).then((response) => {
      if (current) { setData(response.data); setError(""); }
    }).catch((exception) => {
      if (current) setError(exception.response?.data?.detail || "Could not load this information. Please try again.");
    }).finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [path, refreshKey]);
  return { data, items: unwrap(data), error, loading };
}
