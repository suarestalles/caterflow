
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  AUTH_COOKIES,
  getApiBaseUrl,
} from "@/lib/server/auth";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyRequest(
  request: Request,
  context: RouteContext,
) {
  const method = request.method.toUpperCase();
  const requestUrl = new URL(request.url);

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const origin = request.headers.get("origin");

    if (!origin || origin !== requestUrl.origin) {
      return NextResponse.json(
        { message: "Origem da requisição não permitida." },
        { status: 403 },
      );
    }
  }

  const { path } = await context.params;

  if (
    !path.length ||
    path.some((segment) => segment === "." || segment === "..")
  ) {
    return NextResponse.json(
      { message: "Caminho inválido." },
      { status: 400 },
    );
  }

  const cookieStore = await cookies();
  const accessToken = cookieStore.get(AUTH_COOKIES.access)?.value;

  if (!accessToken) {
    return NextResponse.json(
      { message: "Autenticação necessária." },
      { status: 401 },
    );
  }

  const encodedPath = path.map(encodeURIComponent).join("/");
  const target = new URL(
    `${getApiBaseUrl()}/api/v1/${encodedPath}`,
  );

  target.search = requestUrl.search;

  const headers = new Headers();

  headers.set("Authorization", `Bearer ${accessToken}`);

  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");

  if (contentType) headers.set("Content-Type", contentType);
  if (accept) headers.set("Accept", accept);

  let body: ArrayBuffer | undefined;

  if (!["GET", "HEAD"].includes(method)) {
    body = await request.arrayBuffer();
  }

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
    ]) {
      const value = upstream.headers.get(header);

      if (value) responseHeaders.set(header, value);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return NextResponse.json(
      { message: "Erro ao comunicar com a API." },
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
