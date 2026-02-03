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
    "inline-flex items-center justify-center rounded-lg font-semibold shadow-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    primary:
      "border-2 border-vsa-orange-600/30 bg-vsa-orange text-white hover:bg-vsa-orange-600 hover:border-vsa-orange-600 hover:shadow-vsa-orange focus:ring-vsa-orange-500 active:bg-vsa-orange-700",
    ghost:
      "border-2 border-transparent bg-transparent text-slate-700 hover:bg-slate-100 hover:text-slate-900 focus:ring-vsa-orange/50",
    outline:
      "border-2 border-slate-400 bg-white text-slate-700 hover:border-vsa-orange hover:bg-vsa-orange-50/80 hover:text-slate-900 focus:ring-vsa-orange/40",
  } as const;
  const sizes = {
    sm: "h-8 px-3 text-xs rounded-md",
    md: "h-10 px-4 text-sm",
  } as const;

  return <button className={clsx(base, variants[variant], sizes[size], className)} {...props} />;
}

