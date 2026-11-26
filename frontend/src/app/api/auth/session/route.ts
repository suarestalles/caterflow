import { handleSession } from "@/lib/server/auth";

export async function GET() {
  return handleSession();
}