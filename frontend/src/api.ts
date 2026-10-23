const ROOT = import.meta.env?.VITE_API_URL || "";
export async function request<T>(
  path: string,
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  try {
    const response = await fetch(`${ROOT}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.any([
        ...(signal ? [signal] : []),
        AbortSignal.timeout(15000),
      ]),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        typeof error.detail === "string"
          ? error.detail
          : `Request failed (${response.status}). Check your selections and retry.`,
      );
    }
    return await response.json();
  } catch (error) {
    if (signal?.aborted) throw error;
    if (error instanceof DOMException && error.name === "TimeoutError")
      throw new Error("The server took too long to respond. Please retry.");
    throw error;
  }
}
export async function loadJob<T>(
  path: string,
  body: unknown | undefined,
  signal: AbortSignal,
  timeoutMs = 180000,
): Promise<{ id: string; data: T }> {
  const controller = new AbortController();
  const cancel = () => controller.abort(signal.reason);
  signal.addEventListener("abort", cancel, { once: true });
  if (signal.aborted) cancel();
  let timedOut = false;
  const deadline = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const jobSignal = controller.signal;
  try {
    const { job_id } = await request<{ job_id: string }>(path, body, jobSignal);
    while (!jobSignal.aborted) {
      const job = await request<{ status: string; message?: string; data: T }>(
        `/api/jobs/${job_id}`,
        undefined,
        jobSignal,
      );
      if (job.status === "error")
        throw new Error(job.message || "Data is unavailable.");
      if (job.status === "done") return { id: job_id, data: job.data };
      await new Promise<void>((resolve, reject) => {
        const cancelWait = () => {
          clearTimeout(timer);
          jobSignal.removeEventListener("abort", cancelWait);
          reject(new DOMException("Aborted", "AbortError"));
        };
        const timer = setTimeout(() => {
          jobSignal.removeEventListener("abort", cancelWait);
          resolve();
        }, 1200);
        jobSignal.addEventListener("abort", cancelWait, { once: true });
        if (jobSignal.aborted) cancelWait();
      });
    }
    throw new DOMException("Aborted", "AbortError");
  } catch (error) {
    if (timedOut && !signal.aborted)
      throw new Error("Loading exceeded the time limit. Please retry; downloaded data stays cached.");
    throw error;
  } finally {
    clearTimeout(deadline);
    signal.removeEventListener("abort", cancel);
  }
}
