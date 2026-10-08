const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

export function getStoredAuth() {
  return {
    token: localStorage.getItem("lunrea_token"),
    session: localStorage.getItem("lunrea_session"),
  };
}

export function setAuth(token, session = null) {
  localStorage.setItem("lunrea_token", token);
  if (session) localStorage.setItem("lunrea_session", session);
}

export function clearAuth() {
  localStorage.removeItem("lunrea_token");
  localStorage.removeItem("lunrea_session");
}

export async function api(path, options = {}) {
  const { token, session } = getStoredAuth();
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (session) headers.set("X-App-Session", session);

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.blob();

  if (!response.ok) {
    const error = new Error(data?.error || "Request failed.");
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export async function uploadMedia(memoryId, file) {
  const form = new FormData();
  form.append("file", file);
  return api(`/api/memories/${memoryId}/upload`, {
    method: "POST",
    body: form,
  });
}

export async function downloadMedia(mediaId) {
  const { token, session } = getStoredAuth();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (session) headers.set("X-App-Session", session);
  const response = await fetch(`${API_URL}/api/media/${mediaId}`, { headers });
  if (!response.ok) throw new Error("Could not load media.");
  return response.blob();
}
