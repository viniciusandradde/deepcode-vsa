import clsx from "clsx";
import type { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline";
}

export function Badge({ variant = "default", className, ...props }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        variant === "default"
          ? "bg-white/5 text-neutral-300 border border-white/10"
          : "border border-white/10 text-neutral-300",
        className,
      )}
      {...props}
    />
  );
}
