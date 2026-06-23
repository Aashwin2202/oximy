import { useEffect, useRef } from "react";

export function useAutoRefresh(callback: () => void, intervalMs = 30_000) {
  const cbRef = useRef(callback);
  cbRef.current = callback;

  useEffect(() => {
    const id = setInterval(() => cbRef.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
}
