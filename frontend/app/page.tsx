"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

// Client-side redirect (works with static export). The guarded layout sends
// unauthenticated users on to /login.
export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/invoices");
  }, [router]);
  return null;
}
