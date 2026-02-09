import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "outline";
  size?: "sm" | "md";
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-lg font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-obsidian-900 disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    primary:
      "bg-brand-primary text-white hover:bg-brand-primary-dark hover:shadow-glow-orange focus:ring-brand-primary/30 active:bg-vsa-orange-700",
    ghost:
      "bg-transparent text-neutral-300 hover:bg-white/5 hover:text-white focus:ring-brand-primary/30",
    outline:
      "border border-white/10 bg-white/5 text-neutral-300 hover:border-white/20 hover:bg-white/10 hover:text-white focus:ring-brand-primary/30",
  } as const;
  const sizes = {
    sm: "h-8 px-3 text-xs rounded-md",
    md: "h-10 px-4 text-sm",
  } as const;

  return <button className={clsx(base, variants[variant], sizes[size], className)} {...props} />;
}
