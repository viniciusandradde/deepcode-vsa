import clsx from "clsx";
import type { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline";
}

export function Badge({ variant = "default", className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium shadow-sm",
        variant === "default"
          ? "bg-slate-100 text-slate-700"
          : "border-2 border-slate-400 text-slate-700",
        className,
      )}
      {...props}
    />
  );
}

