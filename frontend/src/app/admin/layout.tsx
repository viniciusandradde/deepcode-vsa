"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { PageNavBar } from "@/components/app/PageNavBar";

const NAV_ITEMS = [
  { href: "/admin" as const, label: "Agentes", icon: "bot" },
  { href: "/admin/connectors" as const, label: "Conectores", icon: "plug" },
  { href: "/admin/domains" as const, label: "Domínios", icon: "database" },
] as const;

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-obsidian-950 text-white">
      <PageNavBar />
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">Administração</h1>
          <p className="mt-1 text-sm text-neutral-400">
            Gerencie agentes, conectores e domínios de conhecimento
          </p>
        </div>

        <nav className="mb-8 flex gap-1 rounded-lg border border-white/[0.06] bg-obsidian-900 p-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/admin"
                ? pathname === "/admin"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-primary/10 text-brand-primary border border-brand-primary/30"
                    : "text-neutral-400 hover:text-white hover:bg-white/5",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {children}
      </div>
    </div>
  );
}
