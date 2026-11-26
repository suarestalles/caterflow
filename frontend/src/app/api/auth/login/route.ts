import { handleLogin } from "@/lib/server/auth";

export async function POST(request: Request) {
  return handleLogin(request, "tenant");
}