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
  const base = "inline-flex items-center justify-center rounded-md font-semibold uppercase tracking-[0.25em] transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#0b1526]";
  const variants = {
    primary: "bg-vsa-orange text-white hover:bg-vsa-orange-dark focus:ring-vsa-orange-light shadow-lg shadow-vsa-orange/20",
    ghost: "bg-transparent text-slate-100 hover:bg-white/10 focus:ring-vsa-blue",
    outline: "border border-vsa-blue/40 text-vsa-blue-light hover:border-vsa-blue hover:bg-vsa-blue/10 focus:ring-vsa-blue-light",
  } as const;
  const sizes = {
    sm: "h-8 px-3 text-xs",
    md: "h-10 px-4 text-sm",
  } as const;

  return <button className={clsx(base, variants[variant], sizes[size], className)} {...props} />;
}

