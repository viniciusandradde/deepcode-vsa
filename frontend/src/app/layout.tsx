import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "DeepCode VSA",
  description: "Agente Inteligente para Gestão de TI",
  manifest: "/manifest.json",
  themeColor: "#FF6B35",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "DeepCode VSA",
  },
  viewport: {
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
  },
  icons: {
    icon: "/images/vsa-logo.png",
    apple: "/images/vsa-logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.variable} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}


