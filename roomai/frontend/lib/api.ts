import type {
  AuthResponse,
  Design,
  RoomUploadResponse,
  Style,
  User,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const TOKEN_KEY = "roomai_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

/** Resolve a backend-relative storage path to an absolute URL. */
export function resolveImageUrl(url?: string | null): string {
  if (!url) return "";
  if (url.startsWith("http")) return url;
  return `${API_BASE}${url}`;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = false
): Promise<T> {
  const headers = new Headers(options.headers);
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail: string = res.statusText;
    let code: string | undefined;
    try {
      const data = await res.json();
      // out_of_credits comes back as {error, message}; others as {detail}.
      if (data.error) {
        code = data.error;
        detail = data.message || data.error;
      } else if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (data.detail) {
        detail = JSON.stringify(data.detail);
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, res.status, code);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  signup: (email: string, password: string) =>
    request<AuthResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/auth/me", {}, true),

  uploadRoom: (file: File) => {
    const form = new FormData();
    form.append("image", file);
    return request<RoomUploadResponse>(
      "/rooms",
      { method: "POST", body: form },
      true
    );
  },

  createDesign: (roomId: number, style: Style) =>
    request<Design>(
      `/rooms/${roomId}/designs`,
      { method: "POST", body: JSON.stringify({ style }) },
      true
    ),

  getDesign: (id: number | string) =>
    request<Design>(`/designs/${id}`, {}, true),

  myDesigns: () => request<Design[]>("/users/me/designs", {}, true),
};
