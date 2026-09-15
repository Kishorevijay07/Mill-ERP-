"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useLogout, useMe } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const NAV = [
  { href: "/invoices", label: "Invoices" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: me } = useMe();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => router.replace("/login"),
    });
  }

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="border-b border-border bg-muted/40 md:w-60 md:border-b-0 md:border-r">
        <div className="flex items-center justify-between p-4 md:block">
          <div>
            <p className="text-base font-semibold">
              (RM)<sup>2</sup>
            </p>
            <p className="text-xs text-muted-foreground">GST Invoicing</p>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-2 pb-2 md:flex-col md:px-2">
          {NAV.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-muted",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-border px-4 py-3">
          <div className="text-sm text-muted-foreground">
            {me ? (
              <>
                <span className="font-medium text-foreground">
                  {me.user.full_name}
                </span>
                {" · "}
                {me.roles.join(", ")}
              </>
            ) : null}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            disabled={logout.isPending}
          >
            Sign out
          </Button>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
