
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  AUTH_COOKIES,
  getApiBaseUrl,
} from "@/lib/server/auth";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const PLATFORM_PATHS = new Set([
  "platform-tenants",
  "platform-users",
  "platform-memberships",
]);

const ALLOWED_METHODS = [
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "HEAD",
] as const;

async function proxyRequest(
  request: Request,
  context: RouteContext,
) {
  const method = request.method.toUpperCase();

  if (!ALLOWED_METHODS.includes(method as (typeof ALLOWED_METHODS)[number])) {
    return NextResponse.json(
      { detail: "Método não permitido." },
      { status: 405 },
    );
  }

  const requestUrl = new URL(request.url);

  // Proteção contra CSRF nas operações que alteram dados.
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const origin = request.headers.get("origin");

    if (!origin || origin !== requestUrl.origin) {
      return NextResponse.json(
        { detail: "Origem não permitida." },
        { status: 403 },
      );
    }
  }

  const { path } = await context.params;

  if (
    !path?.length ||
    path.some(
      (segment) =>
        !segment ||
        segment === "." ||
        segment === ".." ||
        segment.includes("/") ||
        segment.includes("\\"),
    )
  ) {
    return NextResponse.json(
      { detail: "Caminho inválido." },
      { status: 400 },
    );
  }

  const cookieStore = await cookies();

  const accessToken = cookieStore.get(
    AUTH_COOKIES.access,
  )?.value;

  const sessionType = cookieStore.get(
    AUTH_COOKIES.type,
  )?.value;

  if (!accessToken) {
    return NextResponse.json(
      { detail: "Autenticação necessária." },
      { status: 401 },
    );
  }

  if (sessionType !== "tenant" && sessionType !== "platform") {
    return NextResponse.json(
      { detail: "Tipo de sessão inválido." },
      { status: 401 },
    );
  }

  const isPlatformRoute = PLATFORM_PATHS.has(path[0]);

  if (
    (isPlatformRoute && sessionType !== "platform") ||
    (!isPlatformRoute && sessionType !== "tenant")
  ) {
    return NextResponse.json(
      { detail: "Sessão incompatível com esta operação." },
      { status: 403 },
    );
  }

  const targetPath = path.map(encodeURIComponent).join("/");

  const needsTrailingSlash =
    path.length === 1 && PLATFORM_PATHS.has(path[0]);
  
  const target = new URL(
    `${getApiBaseUrl()}/api/v1/${targetPath}${needsTrailingSlash ? "/" : ""}`,
  );
  
  target.search = requestUrl.search;

  const headers = new Headers({
    Authorization: `Bearer ${accessToken}`,
  });

  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");

  if (contentType) headers.set("Content-Type", contentType);
  if (accept) headers.set("Accept", accept);

  const body =
    ["GET", "HEAD"].includes(method)
      ? undefined
      : await request.arrayBuffer();

  try {
    const upstream = await fetch(target, {
      method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
    });

    const responseHeaders = new Headers();

    for (const header of [
      "content-type",
      "content-disposition",
      "cache-control",
      "etag",
      "retry-after",
    ]) {
      const value = upstream.headers.get(header);

      if (value) responseHeaders.set(header, value);
    }

    if ([204, 205, 304].includes(upstream.status)) {
      return new NextResponse(null, {
        status: upstream.status,
        headers: responseHeaders,
      });
    }

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return NextResponse.json(
      { detail: "Erro ao comunicar com a API." },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
export const HEAD = proxyRequest;
