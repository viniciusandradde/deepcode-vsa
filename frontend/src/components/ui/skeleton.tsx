import clsx from "clsx";

interface SkeletonProps {
  className?: string;
}

/** Basic shimmer block – uses the `.skeleton` class from globals.css */
export function Skeleton({ className }: SkeletonProps) {
  return <div className={clsx("skeleton", className)} />;
}

/** Preset: single line of text */
export function SkeletonLine({ className }: SkeletonProps) {
  return <Skeleton className={clsx("h-4 w-full rounded", className)} />;
}

/** Preset: circle avatar */
export function SkeletonCircle({ className }: SkeletonProps) {
  return <Skeleton className={clsx("h-10 w-10 rounded-full", className)} />;
}

/** Preset: sidebar session card */
export function SkeletonSessionCard() {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-white/[0.06] bg-obsidian-800 px-3 py-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32 rounded" />
        <Skeleton className="h-4 w-6 rounded-full" />
      </div>
      <Skeleton className="h-3 w-48 rounded" />
    </div>
  );
}

/** Preset: chat message bubble */
export function SkeletonMessage({ align = "left" }: { align?: "left" | "right" }) {
  return (
    <div className={clsx("flex", align === "right" ? "justify-end" : "justify-start")}>
      <div className={clsx(
        "flex flex-col gap-2 rounded-xl border border-white/[0.06] p-4",
        align === "right" ? "w-2/3 bg-brand-primary/5" : "w-3/4 bg-obsidian-800",
      )}>
        <Skeleton className="h-3 w-16 rounded" />
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-5/6 rounded" />
        <Skeleton className="h-4 w-2/3 rounded" />
      </div>
    </div>
  );
}

/** Preset: planning project card */
export function SkeletonProjectCard() {
  return (
    <div className="glass-panel rounded-xl border border-white/[0.06] p-4">
      <div className="flex items-start justify-between mb-3">
        <Skeleton className="h-5 w-40 rounded" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
      <Skeleton className="h-3 w-full rounded mb-2" />
      <Skeleton className="h-3 w-2/3 rounded mb-4" />
      <div className="flex justify-between">
        <Skeleton className="h-3 w-24 rounded" />
        <Skeleton className="h-3 w-16 rounded" />
      </div>
    </div>
  );
}
