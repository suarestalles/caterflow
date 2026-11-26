
import "server-only";

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_BASE_URL = (
  process.env.CATERFLOW_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export const AUTH_COOKIES = {
  access: "caterflow_access",
  refresh: "caterflow_refresh",
  type: "caterflow_session_type",
} as const;

export type SessionType = "tenant" | "platform";

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

const cookieSecurity = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
};

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function backendFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response | null> {
  try {
    return await fetch(`${API_BASE_URL}/api/v1${path}`, {
      ...init,
      cache: "no-store",
    });
  } catch {
    return null;
  }
}

export function setAuthCookies(
  response: NextResponse,
  tokens: TokenResponse,
  sessionType: SessionType,
) {
  response.cookies.set(AUTH_COOKIES.access, tokens.access_token, {
    ...cookieSecurity,
    path: "/",
    maxAge: 15 * 60,
  });

  response.cookies.set(AUTH_COOKIES.refresh, tokens.refresh_token, {
    ...cookieSecurity,
    path: "/api/auth",
    maxAge: 30 * 24 * 60 * 60,
  });

  response.cookies.set(AUTH_COOKIES.type, sessionType, {
    ...cookieSecurity,
    path: "/",
    maxAge: 30 * 24 * 60 * 60,
  });
}

export function clearAuthCookies(response: NextResponse) {
  response.cookies.set(AUTH_COOKIES.access, "", {
    ...cookieSecurity,
    path: "/",
    maxAge: 0,
  });

  response.cookies.set(AUTH_COOKIES.refresh, "", {
    ...cookieSecurity,
    path: "/api/auth",
    maxAge: 0,
  });

  response.cookies.set(AUTH_COOKIES.type, "", {
    ...cookieSecurity,
    path: "/",
    maxAge: 0,
  });
}

async function backendError(response: Response) {
  try {
    const data = await response.json();

    return {
      message:
        typeof data.detail === "string"
          ? data.detail
          : "Não foi possível autenticar.",
    };
  } catch {
    return { message: "Não foi possível autenticar." };
  }
}

export async function handleLogin(
  request: Request,
  sessionType: SessionType,
) {
  let payload: Record<string, unknown>;

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { message: "Corpo da requisição inválido." },
      { status: 400 },
    );
  }

  if (
    typeof payload.email !== "string" ||
    typeof payload.password !== "string" ||
    !payload.email.trim() ||
    !payload.password
  ) {
    return NextResponse.json(
      { message: "Informe email e senha." },
      { status: 400 },
    );
  }

  if (
    sessionType === "tenant" &&
    (typeof payload.tenant_id !== "string" || !payload.tenant_id)
  ) {
    return NextResponse.json(
      { message: "Informe o identificador da empresa." },
      { status: 400 },
    );
  }

  const endpoint =
    sessionType === "tenant" ? "/auth/login" : "/auth/platform/login";

  const backendResponse = await backendFetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!backendResponse) {
    return NextResponse.json(
      { message: "Não foi possível conectar ao servidor." },
      { status: 503 },
    );
  }

  if (!backendResponse.ok) {
    const error = await backendError(backendResponse);

    return NextResponse.json(error, {
      status: backendResponse.status,
    });
  }

  const tokens = (await backendResponse.json()) as TokenResponse;

  const response = NextResponse.json({ authenticated: true });

  setAuthCookies(response, tokens, sessionType);

  return response;
}

export async function handleRefresh() {
  const cookieStore = await cookies();

  const refreshToken = cookieStore.get(AUTH_COOKIES.refresh)?.value;
  const sessionType = cookieStore.get(AUTH_COOKIES.type)?.value;

  if (
    !refreshToken ||
    (sessionType !== "tenant" && sessionType !== "platform")
  ) {
    const response = NextResponse.json(
      { message: "Sessão não encontrada." },
      { status: 401 },
    );

    clearAuthCookies(response);
    return response;
  }

  const backendResponse = await backendFetch("/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!backendResponse) {
    return NextResponse.json(
      { message: "Não foi possível conectar ao servidor." },
      { status: 503 },
    );
  }

  if (!backendResponse.ok) {
    const response = NextResponse.json(
      { message: "Sessão expirada. Entre novamente." },
      { status: 401 },
    );

    clearAuthCookies(response);
    return response;
  }

  const tokens = (await backendResponse.json()) as TokenResponse;

  const response = NextResponse.json({ authenticated: true });

  setAuthCookies(response, tokens, sessionType);

  return response;
}

export async function handleLogout() {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get(AUTH_COOKIES.refresh)?.value;

  if (refreshToken) {
    await backendFetch("/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  const response = new NextResponse(null, { status: 204 });

  clearAuthCookies(response);

  return response;
}

export async function handleSession() {
  const cookieStore = await cookies();

  const accessToken = cookieStore.get(AUTH_COOKIES.access)?.value;
  const refreshToken = cookieStore.get(AUTH_COOKIES.refresh)?.value;
  const sessionType = cookieStore.get(AUTH_COOKIES.type)?.value;

  if (sessionType !== "tenant" && sessionType !== "platform") {
    return NextResponse.json(
      { message: "Sessão não encontrada." },
      { status: 401 },
    );
  }

  const endpoint =
    sessionType === "tenant" ? "/auth/me" : "/auth/platform/me";

  let currentAccessToken = accessToken;
  let rotatedTokens: TokenResponse | null = null;

  if (!currentAccessToken && refreshToken) {
    const refreshResponse = await backendFetch("/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshResponse?.ok) {
      rotatedTokens = (await refreshResponse.json()) as TokenResponse;
      currentAccessToken = rotatedTokens.access_token;
    }
  }

  if (!currentAccessToken) {
    const response = NextResponse.json(
      { message: "Sessão expirada." },
      { status: 401 },
    );

    clearAuthCookies(response);
    return response;
  }

  let backendResponse = await backendFetch(endpoint, {
    headers: {
      Authorization: `Bearer ${currentAccessToken}`,
    },
  });

  if (backendResponse?.status === 401 && refreshToken && !rotatedTokens) {
    const refreshResponse = await backendFetch("/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (refreshResponse?.ok) {
      rotatedTokens = (await refreshResponse.json()) as TokenResponse;

      backendResponse = await backendFetch(endpoint, {
        headers: {
          Authorization: `Bearer ${rotatedTokens.access_token}`,
        },
      });
    }
  }

  if (!backendResponse) {
    return NextResponse.json(
      { message: "Não foi possível conectar ao servidor." },
      { status: 503 },
    );
  }

  if (!backendResponse.ok) {
    const response = NextResponse.json(
      { message: "Sessão inválida." },
      { status: backendResponse.status },
    );

    if (backendResponse.status === 401) {
      clearAuthCookies(response);
    }

    return response;
  }

  const session = await backendResponse.json();
  const response = NextResponse.json(session);

  if (rotatedTokens) {
    setAuthCookies(response, rotatedTokens, sessionType);
  }

  return response;
}
