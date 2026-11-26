import { handleLogout } from "@/lib/server/auth";

export async function POST() {
  return handleLogout();
}