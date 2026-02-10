import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ToastProvider } from "@/components/ui/toast";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "VSA Nexus AI",
  description: "Agente Inteligente para Gestão de TI",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "VSA Nexus AI",
  },
  icons: {
    icon: "/images/vsa-logo.png",
    apple: "/images/vsa-logo.png",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: "#050505",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
        {/* Ambient Light Orbs — crystalline depth */}
        <div className="fixed top-[-100px] left-[-100px] w-[500px] h-[500px] bg-brand-primary/15 blur-[80px] rounded-full pointer-events-none -z-10 animate-float" />
        <div className="fixed bottom-[-50px] right-[-50px] w-[400px] h-[400px] bg-brand-secondary/15 blur-[80px] rounded-full pointer-events-none -z-10 animate-float" style={{ animationDelay: "2s" }} />
        <div className="fixed top-[20%] right-[30%] w-[300px] h-[300px] bg-brand-primary/10 blur-[80px] rounded-full pointer-events-none -z-10 animate-pulse-slow" />
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
