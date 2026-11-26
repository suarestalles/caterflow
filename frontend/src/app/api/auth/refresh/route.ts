import { handleRefresh } from "@/lib/server/auth";

export async function POST() {
  return handleRefresh();
}