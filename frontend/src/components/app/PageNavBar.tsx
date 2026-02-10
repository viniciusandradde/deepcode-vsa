"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageNavBarProps {
  breadcrumbs?: Breadcrumb[];
}

const NAV_LINKS = [
  { label: "Chat", href: "/" },
  { label: "Projetos", href: "/planning" },
  { label: "Scheduler", href: "/automation/scheduler" },
];

export function PageNavBar({ breadcrumbs }: PageNavBarProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <nav className="bg-obsidian-900/80 backdrop-blur-md border-b border-white/[0.06] px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-sm">
          {breadcrumbs && breadcrumbs.length > 0 ? (
            breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-2">
                {i > 0 && <span className="text-neutral-600">/</span>}
                {crumb.href ? (
                  <Link href={crumb.href as "/"} className="text-neutral-400 hover:text-white transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-white font-medium">{crumb.label}</span>
                )}
              </span>
            ))
          ) : (
            <span className="text-white font-medium">VSA Nexus AI</span>
          )}
        </div>

        {/* Cross-links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href as "/"}
              className={clsx(
                "px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                isActive(link.href)
                  ? "bg-brand-primary/15 text-brand-primary"
                  : "text-neutral-500 hover:text-white hover:bg-white/5",
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
