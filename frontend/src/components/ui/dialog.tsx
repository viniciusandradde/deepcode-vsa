"use client";

import { Fragment, ReactNode } from "react";
import clsx from "clsx";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Dialog({ open, onClose, title, children, footer }: DialogProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-md"
        aria-hidden="true"
      />
      <div
        className="relative z-50 w-full max-w-md glass-panel rounded-xl border border-white/[0.06] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-semibold uppercase tracking-wide text-white">
          {title}
        </h2>
        <div className="mb-6 text-sm text-neutral-300">{children}</div>
        {footer && <div className="flex justify-end gap-3">{footer}</div>}
      </div>
    </div>
  );
}
