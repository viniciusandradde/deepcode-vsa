"use client";

import Image from "next/image";
import { useState } from "react";
import clsx from "clsx";

export interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showText?: boolean;
}

const sizeClasses = {
  sm: "h-8 w-auto",
  md: "h-12 w-auto",
  lg: "h-16 w-auto",
  xl: "h-20 w-auto",
};

const textSizeClasses = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
  xl: "text-xl",
};

export function Logo({ size = "md", className, showText = true }: LogoProps) {
  const [imageError, setImageError] = useState(false);

  // Fallback se a imagem não for encontrada
  if (imageError) {
    return (
      <div className={clsx("flex items-center gap-2", className)}>
        <div className={clsx(
          "flex items-center justify-center rounded-lg font-bold text-white",
          sizeClasses[size]
        )} style={{
          background: "var(--vsa-orange-gradient)",
          minWidth: size === "sm" ? "2rem" : size === "md" ? "3rem" : size === "lg" ? "4rem" : "5rem",
        }}>
          <span className={textSizeClasses[size]}>VSA</span>
        </div>
        {showText && (
          <div className="flex flex-col">
            <span className={clsx("font-bold text-white", textSizeClasses[size])}>VSA</span>
            <span className={clsx("text-vsa-blue-light text-xs", size === "sm" ? "text-[10px]" : "")}>
              Soluções em Tecnologia
            </span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={clsx("flex items-center gap-3", className)}>
      <div className={clsx("relative", sizeClasses[size])}>
        <Image
          src="/images/vsa-logo.png"
          alt="VSA Soluções em Tecnologia"
          width={size === "sm" ? 32 : size === "md" ? 48 : size === "lg" ? 64 : 80}
          height={size === "sm" ? 32 : size === "md" ? 48 : size === "lg" ? 64 : 80}
          className="object-contain"
          onError={() => setImageError(true)}
          priority
        />
      </div>
      {showText && (
        <div className="flex flex-col">
          <span className={clsx("font-bold text-white", textSizeClasses[size])}>VSA</span>
          <span className={clsx("text-vsa-blue-light text-xs", size === "sm" ? "text-[10px]" : "")}>
            Soluções em Tecnologia
          </span>
        </div>
      )}
    </div>
  );
}

