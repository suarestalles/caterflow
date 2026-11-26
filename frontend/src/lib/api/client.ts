
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "same-origin",
    })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

async function parseError(response: Response): Promise<ApiError> {
  let message = "Ocorreu um erro ao comunicar com o servidor.";

  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      message = data.detail;
    } else if (typeof data.message === "string") {
      message = data.message;
    }
  } catch {
    // Mantém a mensagem padrão.
  }

  return new ApiError(message, response.status);
}

export type ApiRequestOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
};

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const normalizedPath = path.replace(/^\/+/, "");

  if (
    !normalizedPath ||
    normalizedPath.split("/").some(
      (segment) => segment === "." || segment === "..",
    )
  ) {
    throw new ApiError("Caminho da API inválido.", 400);
  }

  const url = `/api/backend/${normalizedPath}`;

  const headers = new Headers(options.headers);

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  const execute = () =>
    fetch(url, {
      ...options,
      headers,
      credentials: "same-origin",
    });

  let response = await execute();

  if (response.status === 401) {
    const refreshed = await refreshSession();

    if (refreshed) {
      response = await execute();
    }
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
