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
  const base = "inline-flex items-center justify-center rounded-md font-medium shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white";
  const variants = {
    primary: "border-2 border-transparent bg-vsa-orange text-slate-900 hover:bg-vsa-orange-dark focus:ring-vsa-orange-light",
    ghost: "border-2 border-transparent bg-transparent text-slate-900 hover:bg-slate-100 focus:ring-vsa-orange/50",
    outline: "border-2 border-slate-300 text-slate-900 hover:border-vsa-orange/60 hover:text-slate-900 focus:ring-vsa-orange/40",
  } as const;
  const sizes = {
    sm: "h-8 px-3 text-xs",
    md: "h-10 px-4 text-sm",
  } as const;

  return <button className={clsx(base, variants[variant], sizes[size], className)} {...props} />;
}

