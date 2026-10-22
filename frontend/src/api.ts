const ROOT = import.meta.env.VITE_API_URL || "";
export async function request<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${ROOT}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : `Request failed (${response.status}). Check your selections and retry.`,
    );
  }
  return response.json();
}
export async function loadJob<T>(
  path: string,
  body: unknown | undefined,
  signal: AbortSignal,
): Promise<{ id: string; data: T }> {
  const { job_id } = await request<{ job_id: string }>(path, body, signal);
  while (!signal.aborted) {
    const job = await request<{ status: string; message?: string; data: T }>(
      `/api/jobs/${job_id}`,
      undefined,
      signal,
    );
    if (job.status === "error")
      throw new Error(job.message || "Data is unavailable.");
    if (job.status === "done") return { id: job_id, data: job.data };
    await new Promise<void>((resolve, reject) => {
      const cancel = () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      };
      const timer = setTimeout(() => {
        signal.removeEventListener("abort", cancel);
        resolve();
      }, 1200);
      signal.addEventListener("abort", cancel, { once: true });
    });
  }
  throw new DOMException("Aborted", "AbortError");
}
