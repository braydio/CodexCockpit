export function apiBase(): string {
  const raw = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
  return raw && raw.trim()
    ? raw.trim().replace(/\/+$/, "")
    : "http://localhost:8787";
}
