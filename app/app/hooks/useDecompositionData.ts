import { useState, useEffect } from "react";
import type { DecompositionData } from "../types/decomposition";

interface UseDecompositionDataResult {
  data: DecompositionData | null;
  loading: boolean;
  error: string | null;
}

export function useDecompositionData(): UseDecompositionDataResult {
  const [data, setData] = useState<DecompositionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/decomposition.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((json) => {
        setData(json as DecompositionData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { data, loading, error };
}
