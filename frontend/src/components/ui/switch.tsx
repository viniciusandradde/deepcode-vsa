import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

interface SwitchProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  checked: boolean;
  label?: string;
}

export function Switch({ checked, label, className, ...props }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={clsx("flex items-center gap-3", className)}
      {...props}
    >
      <span
        className={clsx(
          "relative inline-flex h-6 w-12 flex-shrink-0 items-center rounded-full border transition-colors",
          checked ? "border-cyan-300 bg-cyan-400/80" : "border-white/12 bg-white/10",
        )}
      >
        <span
          className={clsx(
            "inline-block h-5 w-5 transform rounded-full bg-white transition-transform",
            checked ? "translate-x-5" : "translate-x-1",
          )}
        />
      </span>
      {label ? <span className="text-sm text-slate-200">{label}</span> : null}
    </button>
  );
}

